'''
file containing trade evaluation functions
'''

import random


class TradeEvalObj(object):
    # NOTE input parameters for methods below are in form of list of Objects
    # it is up to the caller to consult this file to figure out what order input arguments are in
    def __init__(self):
        print("eval object created")

    def eval_trade(self, strategy_name: str, arguments_list: list):
        return getattr(self, strategy_name)(arguments_list)

    def eval_random(self, arguments_list):
        rnd_sign = 1.0
        if random.random() > 0.5:
            rnd_sign = -1.0
        return random.random() * rnd_sign

    def moving_avg(self, arguments_list):
        # evaluation based on short term average being above or below long term avg
        technical_analysis_data_dict = arguments_list[0]
        moving_avg_15 = price_str_to_float(technical_analysis_data_dict["15_day_moving_avg"])
        moving_avg_50 = price_str_to_float(technical_analysis_data_dict["50_day_moving_avg"])
        if moving_avg_15 > 0.0 and moving_avg_50 > 0.0:
            moving_avg_delta_15_over_50 = (moving_avg_15 - moving_avg_50)
            moving_avg_15_10_perc = moving_avg_50 * 0.10
            if moving_avg_delta_15_over_50 > moving_avg_15_10_perc:
                return 1.0
            elif moving_avg_delta_15_over_50 < -1.0 * moving_avg_15_10_perc:
                return -1.0
            else:
                return moving_avg_delta_15_over_50 / moving_avg_15_10_perc

    def meb_faber_indicator(self):
        # SPY 200 day moving avg, if SPY closes above it, stay long or get long
        return 0.0


# --- Functions
def price_str_to_float(input_str):
    return float(input_str[0:input_str.index('.') + 3])



