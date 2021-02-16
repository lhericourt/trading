import numpy as np
from indicator.oscillator import Atr, Macd, Rsi, Stochastic, Obv
from indicator.trend import BollingerBands, Adx, Slope
from utils.utils import compute_sign_changement

def atr_features(candles):
    atr = Atr(candles, 'close')
    for avg_type in ['ma', 'ewm', 'wws']:
        candles.loc[:, f'atr_7_{avg_type}'], _ = atr.compute(7, avg_type)
        candles.loc[:, f'atr_14_{avg_type}'], _ = atr.compute(14, avg_type)
        candles.loc[:, f'atr_28_{avg_type}'], _ = atr.compute(28, avg_type)
    return candles


def macd_features(candles):
    macd = Macd(candles, 'close')
    _, _, candles.loc[:, 'macd_hist'] = macd.compute()

    for span in [2, 5, 10]:
        candles[f'macd_change_sign_pos_{span}'], candles[f'macd_change_sign_neg_{span}'] = compute_sign_changement(candles, 'macd_hist', span)
    return candles


def moyenne_mobile_features(candles, remove_ma=True):
    for span in [5, 10, 20, 50, 100, 200]:
        candles[f'ma_{span}'] = candles['close'].rolling(span, min_periods=span).mean()

    # tendances haussières
    candles['above_ma_5'] = np.where(candles['close'] > candles['ma_5'], 1, 0)
    candles['above_ma_200'] = np.where(candles['close'] > candles['ma_200'], 1, 0)
    candles['ma_10_above_ma_100'] = np.where(candles['ma_10'] > candles['ma_100'], 1, 0)
    candles['ma_20_above_ma_50'] = np.where(candles['ma_20'] > candles['ma_50'], 1, 0)

    # tendances baissières
    candles['below_ma_5'] = np.where(candles['close'] < candles['ma_5'], 1, 0)
    candles['below_ma_200'] = np.where(candles['close'] < candles['ma_200'], 1, 0)
    candles['ma_10_velow_ma_100'] = np.where(candles['ma_10'] < candles['ma_100'], 1, 0)
    candles['ma_20_below_ma_50'] = np.where(candles['ma_20'] < candles['ma_50'], 1, 0)

    # Signaux d'achats / ventes
    candles['close_minus_ma_20'] = candles['close'] - candles['ma_20']
    candles['close_minus_ma_200'] = candles['close'] - candles['ma_200']
    candles['ma_50_ma_100'] = candles['ma_50'] - candles['ma_100']
    candles['ma_50_ma_200'] = candles['ma_50'] - candles['ma_200']

    for span in [2, 5, 10]:
        candles[f'close_ma_20_change_sign_pos_{span}'], candles[
            f'close_ma_20_change_sign_neg_{span}'] = compute_sign_changement(candles, 'close_minus_ma_20', span)
        candles[f'close_ma_200_change_sign_pos_{span}'], candles[
            f'close_ma_200_change_sign_neg_{span}'] = compute_sign_changement(candles, 'close_minus_ma_200', span)
        candles[f'ma_50_ma_100_change_sign_pos_{span}'], candles[
            f'ma_50_ma_100_change_sign_neg_{span}'] = compute_sign_changement(candles, 'ma_50_ma_100', span)
        candles[f'ma_50_ma_200_change_sign_pos_{span}'], candles[
            f'ma_50_ma_200_change_sign_neg_{span}'] = compute_sign_changement(candles, 'ma_50_ma_200', span)

    if remove_ma:
        for span in [5, 10, 20, 50, 100, 200]:
            del candles[f'ma_{span}']

    return candles


def rsi_features(candles):
    rsi = Rsi(candles, 'close')
    rsi_val = rsi.compute()
    candles['rsi'] = rsi_val
    candles['rsi_minus_70'] = candles['rsi'] - 70
    candles['rsi_minus_30'] = candles['rsi'] - 30
    for span in [2, 5]:
        _, candles[f'rsi_back_below_70_{span}'] = compute_sign_changement(candles, 'rsi_minus_70', span)
        candles[f'rsi_back_above_30_{span}'], _ = compute_sign_changement(candles, 'rsi_minus_30', span)
    del candles['rsi_minus_70']
    del candles['rsi_minus_30']

    return candles


def stochastic_features(candles):
    stoch = Stochastic(candles)
    candles['stoch'], candles['stoch_ma'], candles['stoch_hist'] = stoch.compute()
    for span in [2, 5]:
        candles[f'stoch_change_sign_pos_{span}'], candles[f'stoch_change_sign_neg_{span}'] = compute_sign_changement(
            candles, 'stoch_hist', span)

    candles['stoch_minus_80'] = candles['stoch'] - 80
    candles['stoch_minus_20'] = candles['stoch'] - 20
    for span in [2, 5]:
        _, candles[f'stoch_back_below_80_{span}'] = compute_sign_changement(candles, 'stoch_minus_80', span)
        candles[f'stoch_back_above_20_{span}'], _ = compute_sign_changement(candles, 'stoch_minus_20', span)

    del candles['stoch_minus_80']
    del candles['stoch_minus_20']

    return candles


def obv_features(candles):
    obv = Obv(candles)
    candles['obv'] = obv.compute()
    candles['obv_pct'] = candles['obv'].pct_change()
    del candles['obv']
    return candles


def bollinger_bands_features(candles):
    _, bb_up, bb_down = BollingerBands(candles, 'close').compute()
    candles['bb_up_minus_close'] = bb_up - candles['close']
    candles['close_minus_bb_down'] = candles['close'] - bb_down
    candles['above_bb_up'] = np.where(candles['close'] > bb_up, 1, 0)
    candles['below_bb_down'] = np.where(candles['close'] < bb_down, 1, 0)
    return candles