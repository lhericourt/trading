from strategy.strategy import StrategyAbstract
from indicator.oscillator import Atr


class ESuperTrend(StrategyAbstract):
    def apply_strategy(self) -> None:
        self.data = self.data.copy()
        atr = Atr(self.data, 'close')
        self.data['e_atr'], _ = atr.compute(span=14, avg_type='ewm')
        self.data['mean'] = (self.data['low'] + self.data['high']) / 2
        self.data['upper_band'] = self.data['mean'] + 3 * self.data['e_atr']
        self.data['lower_band'] = self.data['mean'] - 3 * self.data['e_atr']

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        prev_row = None
        final_upper_band = list()
        final_lower_band = list()
        for row in self.data.itertuples(index=True):
            if prev_row is None:
                prev_row = row
                final_upper_band.append(row.upper_band)
                final_lower_band.append(row.lower_band)
                continue
            if row.upper_band < final_upper_band[-1] or prev_row.close > final_upper_band[-1]:
                final_upper_band.append(row.upper_band)
            else:
                final_upper_band.append(final_upper_band[-1])

            if row.lower_band > final_lower_band[-1] or prev_row.close < final_lower_band[-1]:
                final_lower_band.append(row.lower_band)
            else:
                final_lower_band.append(final_lower_band[-1])

            prev_row = row

        self.data['final_upper_band'] = final_upper_band
        self.data['final_lower_band'] = final_lower_band
        prev_row = None
        super_trend = list()
        for row in self.data.itertuples(index=True):
            if prev_row is None:
                prev_row = row
                super_trend.append(row.final_upper_band)
                continue
            if super_trend[-1] == prev_row.final_upper_band and row.close <= row.final_upper_band:
                super_trend.append(row.final_upper_band)
            elif super_trend[-1] == prev_row.final_upper_band and row.close > row.final_upper_band:
                super_trend.append(row.final_lower_band)
            elif super_trend[-1] == prev_row.final_lower_band and row.close >= row.final_lower_band:
                super_trend.append(row.final_lower_band)
            elif super_trend[-1] == prev_row.final_lower_band and row.close < row.final_lower_band:
                super_trend.append(row.final_upper_band)
            prev_row = row

        self.data['super_trend'] = super_trend

        self._reinit_data()
        self.stop_loss.data = self.data
        nb_prev = 3
        self.prev_rows = nb_prev * [None]

        stop_loss, take_profit = 0, 0

        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, nb_prev):
                self._do_nothing(row, 0, 0)
                self._do_common_processes(row, nb_prev, first_rows=True)
                continue

            if all([x.close < x.super_trend for x in self.prev_rows]) and row.close > row.super_trend:
                self.buy_signal = True
            else:
                self.buy_signal = False

            if all([x.close > x.super_trend for x in self.prev_rows]) and row.close < row.super_trend:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

