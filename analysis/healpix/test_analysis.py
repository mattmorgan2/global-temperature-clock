"""Geometry/distance unit checks; full-run reconciliations live in validation.json."""
import math
import unittest
import numpy as np
from shapely.geometry import Point, box
from analyze import R, boundary_distance_km, chord_km, pixel_polygon, spherical_area, vectors
import healpy as hp


class GeometryTests(unittest.TestCase):
    def test_requested_grid_sizes_and_nested_hierarchy(self):
        self.assertEqual([hp.nside2npix(n) for n in (1,2,4,8)],[12,48,192,768])
        lon=np.array([-179.9,-90,0,45,179.9]);lat=np.array([-89,-40,0,40,89])
        for n in (1,2,4):
            parent=hp.ang2pix(n,lon,lat,nest=True,lonlat=True)
            child=hp.ang2pix(n*2,lon,lat,nest=True,lonlat=True)
            np.testing.assert_array_equal(parent,child//4)
            np.testing.assert_array_equal(parent,hp.ang2pix(n,lon+360,lat,nest=True,lonlat=True))

    def test_global_area_and_polar_dateline_cells(self):
        areas=[]
        for p in range(12):
            geom=pixel_polygon(1,p,256)
            self.assertTrue(geom.is_valid)
            area=spherical_area(geom)
            self.assertAlmostEqual(area/(4*math.pi*R**2/12),1,delta=4e-6)
            lon,lat=hp.pix2ang(1,p,nest=True,lonlat=True)
            self.assertTrue(geom.covers(Point((lon+180)%360-180,lat)))
            areas.append(area)
        self.assertAlmostEqual(sum(areas)/(4*math.pi*R**2),1,delta=4e-6)

    def test_known_spherical_distances(self):
        a=vectors(np.array([0.]),np.array([0.]))[0]
        b=vectors(np.array([90.]),np.array([0.]))[0]
        self.assertAlmostEqual(float(chord_km(np.linalg.norm(a-b))),math.pi*R/2,places=7)
        self.assertAlmostEqual(float(chord_km(2)),math.pi*R,places=7)
        self.assertEqual(float(chord_km(0)),0)

    def test_coastal_land_is_not_whole_cell_and_lake_is_removed(self):
        cell=pixel_polygon(1,4)
        island=box(-.5,-.5,.5,.5)
        lake=box(-.25,-.25,.25,.25)
        land=island.difference(lake).intersection(cell)
        self.assertGreater(spherical_area(land),0)
        self.assertLess(spherical_area(land),spherical_area(cell)*.001)
        self.assertAlmostEqual(spherical_area(land)/spherical_area(island),.75,delta=.0001)
        self.assertFalse(land.contains(Point(0,0)))

    def test_adjacent_cells_can_have_close_boundary_candidates(self):
        lon=np.array([44.99,45.01]);lat=np.array([0.,0.])
        labels=hp.ang2pix(1,lon,lat,nest=True,lonlat=True)
        self.assertNotEqual(labels[0],labels[1])
        self.assertIn(labels[1],hp.get_all_neighbours(1,int(labels[0]),nest=True))
        v=vectors(lon,lat)
        self.assertLess(float(chord_km(np.linalg.norm(v[0]-v[1]))),3)
        for i in (0,1):self.assertLess(boundary_distance_km(v[i],pixel_polygon(1,int(labels[i]))),2)


if __name__=='__main__':unittest.main()
