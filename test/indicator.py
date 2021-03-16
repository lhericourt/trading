from pathlib import Path
from proboscis.asserts import assert_equal
from proboscis import test

import pandas as pd

from indicator.performance import Expectancy
from indicator.risk import RiskRewardRatio

data = pd.read_csv(Path.cwd() / 'trading' / 'test' / 'data' / 'performance_risk_01.csv', sep=';')


@test
def test_expectancy():
    exp = Expectancy(data)
    exp.compute(trade_size=1)
    print(exp.result)
    assert_equal(exp.result['NbTrades'], 5)
    assert_equal(exp.result['HitRatio'], 60.0)
    assert_equal(exp.result['Expectancy'], 0.9)
    assert_equal(exp.result['ProfitFactor'], 2.5)


@test
def test_risk_reward_ratio():
    rrr = RiskRewardRatio(data)
    rrr.compute()
    print(rrr.result)
    assert_equal(rrr.result['RiskRewardRatio'], 2.04)


test_expectancy()
test_risk_reward_ratio()