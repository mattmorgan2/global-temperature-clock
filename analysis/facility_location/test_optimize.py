"""Independent small-problem checks for the exploratory p-median optimizer."""
import itertools
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import json
import numpy as np
from optimize import best_swap,greedy,make_distances,objective,refine,vectors,R


class FacilityTests(unittest.TestCase):
    def test_greedy_recovers_two_cluster_solution(self):
        d=np.array([[0,0,10,10],[10,10,0,0],[5,5,5,5]],dtype=np.float32)
        chosen,costs=greedy(d,2)
        self.assertEqual(set(chosen),{0,1})
        self.assertEqual(costs[-1],0)
        self.assertGreaterEqual(costs[0],costs[1])

    def test_dense_candidate_duplicates_do_not_give_land_extra_weight(self):
        d=np.array([[0,100],[0,100],[0,100],[100,0]],dtype=np.float32)
        chosen,_=greedy(d,2)
        self.assertIn(3,chosen)
        self.assertEqual(objective(d,chosen),0)

    def test_best_swap_matches_brute_force(self):
        rng=np.random.default_rng(123)
        for _ in range(10):
            d=rng.uniform(0,20,(9,17)).astype(np.float32)
            chosen=[0,1,2]
            add,remove,delta=best_swap(d,chosen)
            before=objective(d,chosen)
            alternatives=[]
            for candidate in range(3,9):
                for slot in range(3):
                    proposal=chosen.copy();proposal[slot]=candidate
                    alternatives.append((objective(d,proposal)-before,candidate,slot))
            expected=min(alternatives)
            self.assertAlmostEqual(delta,min(0,expected[0]),places=5)
            if add is not None:
                proposal=chosen.copy();proposal[remove]=add
                self.assertAlmostEqual(objective(d,proposal)-before,expected[0],places=5)

    def test_refinement_improves_and_preserves_unique_size(self):
        d=np.array([[0,0,10,10],[10,10,0,0],[5,5,5,5],[3,3,8,8]],dtype=np.float32)
        selected,entered,trace,converged,delta=refine(d,[2,3],max_swaps=10)
        self.assertEqual(set(selected),{0,1})
        self.assertEqual(len(set(selected)),2)
        self.assertEqual(len(entered),2)
        self.assertTrue(converged)
        self.assertEqual(objective(d,selected),0)
        self.assertTrue(all(r['training_mean_after_km']<r['training_mean_before_km'] for r in trace))

    def test_swap_limit_is_reported_as_nonconvergence(self):
        d=np.array([[0,0,10,10],[10,10,0,0],[5,5,5,5]],dtype=np.float32)
        _,_,trace,converged,delta=refine(d,[0,2],max_swaps=0)
        self.assertFalse(converged)
        self.assertLess(delta,0)
        self.assertEqual(trace,[])

    def test_reproducible_geographic_ties(self):
        d=np.array([[2,2],[2,2],[8,8]],dtype=np.float32)
        a,trace=greedy(d,1);b,_=greedy(d,1)
        self.assertEqual(a,b);self.assertEqual(a,[0])

    def test_dateline_and_antipodes(self):
        facilities=vectors(np.array([179.,0.]),np.array([0.,0.]))
        demand=vectors(np.array([-179.,180.]),np.array([0.,0.]))
        d=make_distances(facilities,demand)
        self.assertAlmostEqual(float(d[0,0]),R*np.deg2rad(2),places=3)
        self.assertAlmostEqual(float(d[1,1]),R*np.pi,places=2)
        self.assertEqual(d.dtype,np.float32)

    def test_maps_keep_each_panel_station_markers_separate(self):
        from optimize import plot_maps
        import matplotlib.figure
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            cache=root/'distances.npz';np.savez_compressed(cache,distances_km=np.ones(12))
            stations=[{'longitude':-100,'latitude':30},{'longitude':0,'latitude':0},{'longitude':100,'latitude':-30}]
            networks={(70,n):{'distance_path':cache,'metrics':{'land_mean_km':1},'rows':stations[:n]} for n in (2,3)}
            with patch('optimize.THRESHOLDS',(70,)),patch('optimize.SIZES',(2,3)),patch.object(matplotlib.figure.Figure,'savefig'):
                plot_maps(root/'maps',networks,np.arange(12),1)
            result=json.loads((root/'map-validation.json').read_text())
            self.assertEqual(result[0]['markers_per_panel'],[2,3])

    def test_greedy_determinism_and_mean_not_max_objective(self):
        d=np.array([[0,0,0,20],[6,6,6,6]],dtype=np.float32)
        chosen,_=greedy(d,1)
        self.assertEqual(chosen,[0]) # mean 5, though worse maximum distance


if __name__=='__main__':unittest.main()
