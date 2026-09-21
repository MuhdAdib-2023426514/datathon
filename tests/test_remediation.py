"""Independent boundary and missing-evidence checks for remediation gates."""
import numpy as np
import pytest
from src.ingestion.numeric import parse_observation
from src.analytics.pareto import pareto_evidence
from src.scenarios.monte_carlo import MonteCarloSimulator

@pytest.mark.parametrize('cell,status', [(None,'missing'), ('','missing'), ('-','suppressed_or_unavailable'), ('bad','invalid'), (float('inf'),'invalid')])
def test_source_absence(cell,status):
    value, actual = parse_observation(cell)
    assert np.isnan(value) and actual == status

def test_source_zero_is_observed():
    assert parse_observation(0) == (0.0, 'observed')

def test_pareto_complete_only():
    complete, ranks = pareto_evidence([[2,2], [1,1], [2,2], [100,np.nan], [np.inf,4], [0,0]])
    assert complete.tolist() == [True,True,True,False,False,True]
    assert ranks[:3].tolist() == [1,3,1]
    assert np.isnan(ranks[3:5]).all()

@pytest.mark.parametrize('reach,extension', [(0,0), (0,0.5), (0.15,0)])
def test_mc_zero_policy(reach,extension):
    result = MonteCarloSimulator().simulate_corridor_uncertainty('Selangor','Melaka',affected_share=reach,delta_alos=extension,n_simulations=100)
    assert result['mean']['additional_nights'] == 0
    assert result['mean']['potential_gva_rm_m'] == 0

def test_mc_missing_capacity_unknown():
    mc=MonteCarloSimulator(); mc.df_cap=mc.df_cap.iloc[:0]
    result=mc.simulate_corridor_uncertainty('Selangor','Melaka',n_simulations=100)
    assert result['prob_capacity_breach'] is None

@pytest.mark.parametrize('field,value', [('delta_alos',float('nan')),('affected_share',-1),('guests_per_room',0),('n_simulations',0)])
def test_mc_invalid(field,value):
    with pytest.raises(ValueError):
        MonteCarloSimulator().simulate_corridor_uncertainty('Selangor','Melaka',**{field:value})

def test_mc_missing_vai_unavailable():
    mc=MonteCarloSimulator(); mc.national_accom_vai=None
    assert mc.simulate_corridor_uncertainty('Selangor','Melaka')['status']=='UNAVAILABLE'

def test_mc_local_rng():
    np.random.seed(12); expected=np.random.random()
    np.random.seed(12)
    mc=MonteCarloSimulator(); mc.simulate_corridor_uncertainty('Selangor','Melaka',n_simulations=100)
    assert np.random.random() == expected
