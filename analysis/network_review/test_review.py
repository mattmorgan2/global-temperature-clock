"""Fixture-based inspection checks; no downloads or optimization."""
import unittest,tempfile
from pathlib import Path
from datetime import date
import numpy as np
from review import inspect_daily,incomplete_runs,neighbors,radius_summary,substantial

SID='US000000001'
def record(year,month,element,values):
    cells=[]
    for day in range(1,32):
        value,qflag=values.get(day,(-9999,' '))
        cells.append(f'{value:5d}H{qflag}S')
    return f'{SID}{year:04}{month:02}{element}'+''.join(cells)+'\n'


class ReviewTests(unittest.TestCase):
    def test_longest_gap_ties_are_preserved_and_earliest_first(self):
        runs=incomplete_runs([True,False,False,True,False,False,True,False],date(2000,1,1))
        self.assertEqual(runs,[{'start':'2000-01-02','end':'2000-01-03','days':2},
                               {'start':'2000-01-05','end':'2000-01-06','days':2},
                               {'start':'2000-01-08','end':'2000-01-08','days':1}])

    def test_leap_day_and_gap_across_months(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.dly'
            path.write_text(''.join(record(2000,m,e,{d:(100,' ')}) for m,d in ((2,27),(3,2)) for e in ('TMAX','TMIN')))
            metrics,runs,_=inspect_daily(path,SID,date(2000,2,27),date(2000,3,2))
            self.assertEqual(metrics['total_calendar_days'],5)
            self.assertEqual(metrics['both_valid_days'],2)
            self.assertEqual(runs,[{'start':'2000-02-28','end':'2000-03-01','days':3}])

    def test_qc_and_missing_element_and_endpoint_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.dly'
            path.write_text(record(1999,12,'TMAX',{1:(100,'X')})+
                record(2000,1,'TMAX',{1:(100,'?'),2:(100,' ')})+
                record(2000,1,'TMIN',{1:(100,' '),2:(100,' ')}))
            metrics,runs,_=inspect_daily(path,SID,date(2000,1,1),date(2000,1,3))
            self.assertEqual(metrics['both_valid_days'],1)
            self.assertEqual(metrics['qc_rejected_tmax_days'],1)
            self.assertEqual(metrics['incomplete_days'],2)
            self.assertEqual(metrics['tmax_first_observed_year'],1999)
            self.assertEqual(metrics['tmax_first_valid_year'],2000)
            self.assertEqual(len(runs),2)

    def test_complete_record_has_no_gap_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.dly'
            path.write_text(''.join(record(2000,1,e,{1:(100,' ')}) for e in ('TMAX','TMIN')))
            metrics,runs,longest=inspect_daily(path,SID,date(2000,1,1),date(2000,1,1))
            self.assertEqual(metrics['longest_gap_start'],'')
            self.assertEqual(metrics['longest_gap_tied_run_count'],0)
            self.assertEqual(runs,[]);self.assertEqual(longest,[])

    def test_neighbor_counts_self_exclusion_pools_and_inclusive_radius(self):
        def station(sid,percent):
            return {'station_id':sid,'station_name':sid,'country_name':'TEST','latitude':'0','longitude':'0',
                    'both_valid_days':str(percent),'total_calendar_days':'100','both_valid_percent':str(percent)}
        self_station=station('A',70)
        others=[self_station,station('B',95),station('C',60),station('D',80)]
        nearby=neighbors(self_station,others,np.array([0,100,20,200]))
        self.assertEqual(len(nearby),3)
        self.assertEqual(radius_summary(nearby,50)['count'],0)
        self.assertEqual(radius_summary(nearby,50,False)['count'],1)
        self.assertEqual(radius_summary(nearby,100)['count'],1)
        self.assertEqual(radius_summary(nearby,100)['highest_completeness_station_id'],'B')
        self.assertEqual(radius_summary(nearby,250)['count'],2)

    def test_substantial_gain_uses_unrounded_day_counts(self):
        station={'both_valid_days':'13000','total_calendar_days':'18263'}
        nearby=[{'distance_km':100,'candidate_eligible_70pct':True,'candidate_both_valid_days':13913},
                {'distance_km':99,'candidate_eligible_70pct':True,'candidate_both_valid_days':13914}]
        self.assertEqual(substantial(station,nearby),[nearby[1]])

    def test_zero_neighbors_is_missing_maximum_not_zero_percent(self):
        result=radius_summary([],100)
        self.assertEqual(result['count'],0)
        self.assertEqual(result['highest_completeness_percent'],'')


if __name__=='__main__':unittest.main()
