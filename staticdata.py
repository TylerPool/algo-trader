"""
module for generating data fields that can be derived for every trading day
and do not rely on inputs from trading simulation

Tyler Pool
2022
"""


def get_static_data_fields(stock_data_history_obj,
                           number_of_trading_days):

    trading_day_object_list = stock_data_history_obj.trading_day_object_list

    # date column
    for trading_day_obj in trading_day_object_list:
        trading_day_obj.technical_analysis_data['date'] = trading_day_obj.date

    # 15 day moving avg
    moving_avg_length = 15
    for i in range(number_of_trading_days):
        if i > moving_avg_length:
            closing_price_from_all_days = stock_data_history_obj.get_closing_prices()
            moving_avg = sum(closing_price_from_all_days[i:i + moving_avg_length]) / moving_avg_length
            trading_day_object_list[i].technical_analysis_data['15_day_moving_avg'] = moving_avg
        else:
            trading_day_object_list[i].technical_analysis_data['15_day_moving_avg'] = 0.0

    # 50 day moving avg
    moving_avg_length = 50
    for i in range(number_of_trading_days):
        if i > moving_avg_length:
            closing_price_from_all_days = stock_data_history_obj.get_closing_prices()
            moving_avg = sum(closing_price_from_all_days[i:i + moving_avg_length]) / moving_avg_length
            trading_day_object_list[i].technical_analysis_data['50_day_moving_avg'] = moving_avg
        else:
            trading_day_object_list[i].technical_analysis_data['50_day_moving_avg'] = 0.0

    return trading_day_object_list
