import pytest
from scientific.ranking import percentile_scores,oil_indices,multi_target

def test_percentiles_and_ties():
    assert percentile_scores({1:-8,2:-6,3:-4})=={1:1.,2:.5,3:0.}
    assert percentile_scores({1:-8,2:-8})=={1:.5,2:.5}
    assert percentile_scores({1:-8})=={1:.5}

def test_abundance_changes_priority_and_coverage():
    a=oil_indices({1:[{'compound_id':1,'percentage':80},{'compound_id':2,'percentage':10},{'compound_id':3,'percentage':5}]},{1:-8,2:-4})[0]
    b=oil_indices({1:[{'compound_id':1,'percentage':10},{'compound_id':2,'percentage':80}]},{1:-8,2:-4})[0]
    assert a['index']==pytest.approx(80/90)
    assert b['index']==pytest.approx(10/90)
    assert a['reported_peak_area_percent']==95
    assert a['screened_peak_area_percent']==90
    assert a['sensitivity_min']<a['index']<a['sensitivity_max']

def test_missing_target_does_not_renormalize():
    results={1:[{'profile_id':1,'index':.9}],2:[{'profile_id':1,'index':None}]}
    assert multi_target(results,{1:1,2:1})[0]['combined_index'] is None
    assert multi_target(results,{1:1,2:0})[0]['combined_index']==.9

def test_invalid_weights_and_duplicate_records():
    with pytest.raises(ValueError):multi_target({}, {1:-1})
    result=oil_indices({1:[{'compound_id':1,'percentage':50}]*2,2:[{'compound_id':1,'percentage':80}]},{1:-8})
    assert next(r for r in result if r['profile_id']==1)['index'] is None
    assert 'duplicate' in next(r for r in result if r['profile_id']==1)['warning']
    assert next(r for r in result if r['profile_id']==2)['index']==.5

