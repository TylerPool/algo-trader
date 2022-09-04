"""
Algorithmic Trading Test Tool
Tyler Pool
2022
"""

import csv
import os.path
import tradeeval
import staticdata
import buystrat
import sellstrat
from datetime import datetime, timedelta

# --- Constants
# TODO: replace hard-coding of variables below with loading from file
STOCK_DATA_FILE_PATH = 'input/stocks/'
STATIC_DATA_FILE_PATH = 'input/static data/'
FILE_EXTENSION_TYPE = '.csv'
TICKER_SYMBOL_LIST = {'SPY', 'GLD', 'AMZN', 'RH', 'XOM', 'WM'}
FILE_COLUMN_WIDTH = 7
INITIAL_CASH_BALANCE = 10000
HIGH_DATE = "9999-12-31"
FIRST_TRADING_DAY = '2014-11-17'
LAST_TRADING_DAY = "2019-11-14"
TRADE_EVAL_STRAT = "eval_random"
BUY_STRAT = "highscore"
SELL_STRAT = "lowscore"
STATIC_DATA_DERIVED_FIELDS = ['date', '15_day_moving_avg', '50_day_moving_avg']


# --- classes
class Portfolio:
    def __init__(self, initial_balance):
        self.cash_balance = initial_balance
        self.stock_shares = []
        self.trade_history = []

    def __repr__(self):
        share_dict = {}
        for symbol in TICKER_SYMBOL_LIST:
            share_dict[symbol] = self.get_share_qty_by_symbol(symbol)
        return str(share_dict)

    def __str__(self):
        share_dict = {}
        for symbol in TICKER_SYMBOL_LIST:
            share_dict[symbol] = self.get_share_qty_by_symbol(symbol)
        return str(share_dict)

    def get_trade_history_str(self):
        trade_history_string = ""
        for trade in self.trade_history:
            trade_history_string += str(trade) + "\n"
        return trade_history_string

    def get_share_qty_by_symbol(self, symbol):
        share_qty = 0
        for share in self.stock_shares:
            if share.symbol == symbol:
                share_qty += 1
        return share_qty

    def buy_share(self, symbol, date, price, qty):
        for i in range(qty):
            self.stock_shares.append(StockShare(symbol, price, date))
            self.cash_balance -= price
        self.trade_history.append(list_to_str(["On ",
                                               date,
                                               ": Buy ",
                                               qty,
                                               " x ",
                                               symbol,
                                               " @ $",
                                               price,
                                               " cash = $",
                                               self.cash_balance]))

    def sell_share(self, symbol, date, price, qty, sale_type):
        # Method assumes that following:
        # - verification such as price being correct and qty of shares actually owned is done by the caller
        # - share list sorted by trade date
        # list of sale types:
        # - FIFO = first in, first out
        if sale_type == "FIFO":
            shares_sold = 0
            remaining_shares_list = []
            # TODO: make loop below more efficient
            for share in self.stock_shares:
                if share.symbol == symbol:
                    if shares_sold < qty:
                        self.cash_balance += price
                        shares_sold += 1
                    else:
                        remaining_shares_list.append(share)
                else:
                    remaining_shares_list.append(share)
            self.stock_shares = remaining_shares_list
            self.trade_history.append(list_to_str(["On ",
                                                   date,
                                                   ": Sell ",
                                                   qty,
                                                   " x ",
                                                   symbol,
                                                   " @ $",
                                                   price,
                                                   " cash = $",
                                                   self.cash_balance]))
            if self.stock_shares == None:
                self.stock_shares = []

    def execute_buy_strategy(self, potential_trades_by_evaluation_score, stock_history_data_object_list, day):
        buy_order = buystrat.get_buy_order(BUY_STRAT, potential_trades_by_evaluation_score)
        if len(buy_order) > 0:
            for order_symbol in buy_order.keys():
                buy_qty = buy_order[order_symbol]
                buy_symbol = order_symbol
                buy_price = get_closing_price(stock_history_data_object_list,
                                              buy_symbol,
                                              day)
                if self.cash_balance > (buy_qty * buy_price):
                    self.buy_share(buy_symbol, "Day " + str(day), buy_price, buy_qty)

    def execute_sell_strategy(self,
                              potential_trades_by_evaluation_score,
                              stock_history_data_object_list,
                              day):

        sell_order = sellstrat.get_sell_order(SELL_STRAT, potential_trades_by_evaluation_score)
        if len(sell_order) > 0:
            for order_symbol in sell_order:
                sell_qty = sell_order[order_symbol]
                sell_symbol = order_symbol
                sell_price = get_closing_price(stock_history_data_object_list,
                                               sell_symbol,
                                               day)
                if self.get_share_qty_by_symbol(sell_symbol) >= sell_qty:
                    self.sell_share(sell_symbol,
                                         "Day " + str(day),
                                         sell_price,
                                         sell_qty,
                                         "FIFO")


class StockDataHistory:
    def __init__(self, symbol, begin, end):
        self.symbol = symbol
        self.first_day = begin
        self.last_day = end
        self.trading_day_object_list = []

    def __str__(self):
        return "Stock Data History for: " + str(self.symbol)

    def __repr__(self):
        return "Stock Data History for: " + str(self.symbol)

    def get_closing_prices(self):
        closing_prices = []
        for day in self.trading_day_object_list:
            closing_prices.append(day.close)
        return closing_prices

    def populate_stock_historical_data(self):
        # using Yahoo finance historical data website
        # manually downloading csv files - TODO transition to web service to retrieve data
        # historical data csv file format:
        # columns: 0=date, 1=open, 2=high, 3=low, 4=close, 5=adj close, 6=volume
        # 0 row is column titles
        print("loading historic price data for ticker: " + self.symbol)
        historical_data = stockdata_csv_to_list_by_symbol(self.symbol)
        historical_data = historical_data[1:]  # remove col tile row
        print("row count = " + str(len(historical_data)))
        for day_row in historical_data:
            if len(day_row) == FILE_COLUMN_WIDTH:
                self.trading_day_object_list.append(TradingDay(self.symbol,
                                                               day_row[0],
                                                               price_str_to_float(day_row[1]),
                                                               price_str_to_float(day_row[4]),
                                                               day_row[6]))

    def populate_technical_analysis_data(self, duration: int):
        # determine if static data fields used for technical analysis have already been generated
        # or need to be populated and saved
        file_name = STATIC_DATA_FILE_PATH + self.symbol + ' SD.csv'
        static_data_write_required = False
        static_fields_list = []
        all_trading_days = self.trading_day_object_list
        number_of_trading_days = len(all_trading_days)

        if os.path.exists(file_name):
            # validate that existing static data file meets date criteria for
            with open(file_name, newline='') as csvfile:
                static_data_str_list = list(csv.reader(csvfile, delimiter=' ', quotechar='|'))
                for row_as_str in static_data_str_list:
                    row_as_list = row_as_str[0].split(',')
                    static_fields_list.append(row_as_list)
            if len(static_fields_list) - 1 != duration:
                static_data_write_required = True
            else:
                for required_field in STATIC_DATA_DERIVED_FIELDS:
                    if required_field not in static_fields_list[0]:
                        static_data_write_required = True
                # validate date range
                if static_fields_list[0][0] == 'date':
                    if static_fields_list[1][0] != FIRST_TRADING_DAY or static_fields_list[-1][0] != LAST_TRADING_DAY:
                        static_data_write_required = True
        else:
            static_data_write_required = True

        if static_data_write_required:
            # generate and save static data used for technical analysis
            self.trading_day_object_list = staticdata.get_static_data_fields(self,
                                                                             number_of_trading_days)
            write_static_data_fields(self.trading_day_object_list, self.symbol)
        else:
            # all required static data fields can be loaded from existing file
            # reminder that width of static field list and list of required static fields determined to be == above
            # remove first static fields row that contains the col names
            for day_number in range(number_of_trading_days):
                for col_num in range(len(static_fields_list[0])):
                    col_name = static_fields_list[0][col_num]
                    self.trading_day_object_list[day_number].technical_analysis_data[col_name] = static_fields_list[day_number + 1][col_num]

    def get_closing_price(self, day):
        return self.trading_day_object_list[day].close


class TradingDay:
    def __init__(self, symbol="", date="", open_price=0.0, close_price=0.0, volume=0):
        self.symbol = symbol
        self.date = date
        self.open = open_price
        self.close = close_price
        self.volume = volume
        self.technical_analysis_data = {}

    def __str__(self):
        return "date = " + str(self.date) + ", open = " + str(self.open)

    def __repr__(self):
        return list_to_str(['Trading Day Object: ', self.symbol,
                            '\n date = ', self.date,
                           '\n open-close-vol = ', self.open, '-', self.close, '-', self.volume,
                            '\n technical data dict:\n',
                            self.technical_analysis_data])


class StockShare:
    def __init__(self, symbol, buy_price, buy_date):
        self.symbol = symbol
        self.buy_price = buy_price
        self.buy_date = buy_date
        self.sell_price = 0.0
        self.sell_date = HIGH_DATE


# --- Functions
# --- --- Basic Operation Functions
def price_str_to_float(input_str):
    return float(input_str[0:input_str.index('.') + 3])


def list_to_str(input_list: list):
    output_string = ""
    if len(input_list) > 0:
        for item in input_list:
            output_string += str(item)
    return output_string


def get_date_diff_days(first_day_str: str, last_day_str: str):
    first_day_date_obj = datetime.strptime(first_day_str, '%Y-%m-%d')
    last_day_date_obj = datetime.strptime(last_day_str, '%Y-%m-%d')
    number_of_days_in_data_range = (last_day_date_obj - first_day_date_obj).days
    if number_of_days_in_data_range > 0:
        return number_of_days_in_data_range
    else:
        return 0


# --- --- Data Functions
def stockdata_csv_to_list_by_symbol(symbol):
    output_list = []
    with open(STOCK_DATA_FILE_PATH + symbol + FILE_EXTENSION_TYPE, newline='') as csvfile:
        historical_data_str_list = list(csv.reader(csvfile, delimiter=' ', quotechar='|'))
        for row_as_str in historical_data_str_list:
            row_as_list = row_as_str[0].split(',')
            output_list.append(row_as_list)
    return output_list


def get_static_data_is_valid(stock_history_data_object_list: list):
    # verify date range and return number of rows of trading data
    trading_day_qty = -1
    for stock_history_data_object in stock_history_data_object_list:
        file_length = len(stock_history_data_object.trading_day_object_list)
        if trading_day_qty == -1:
            trading_day_qty = file_length
        if (stock_history_data_object.first_day != FIRST_TRADING_DAY or
                stock_history_data_object.last_day != LAST_TRADING_DAY or
                file_length != trading_day_qty):
            return 0

    return trading_day_qty


def write_static_data_fields(static_field_row_list: list, symbol: str):
    # static_field_row_list is list of dicts
    # each dict row should have keys for all static derived (i.e. technical analysis) fields
    with open(STATIC_DATA_FILE_PATH + symbol + ' SD.csv', 'w', newline='') as csvfile:
        fieldnames = STATIC_DATA_DERIVED_FIELDS
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for trading_day_object in static_field_row_list:
            writer.writerow(trading_day_object.technical_analysis_data)

    return True


# --- --- Trading Functions
def get_comparison_par(cash, days):
    # using purchase of SPY S&P 500 as par to calculate alpha
    # starting price on 11-17-14 = 201.66
    # final price on 11-15-19 = 311.79
    SPY_history_list = stockdata_csv_to_list_by_symbol("SPY")
    initial_price = price_str_to_float(SPY_history_list[1][1])
    final_price = price_str_to_float(SPY_history_list[days][4])
    qty = cash % initial_price
    starting_balance = cash - (qty * initial_price)
    final_balance = starting_balance + (qty * final_price)
    return final_balance


def get_closing_price(all_stocks_historical_data, symbol, day):
    for stock_historical_data in all_stocks_historical_data:
        if stock_historical_data.symbol == symbol:
            return stock_historical_data.trading_day_object_list[day].close


# --- --- Primary Function
def run_back_test(print_to_console: bool,
                  save_results: bool):

    if print_to_console:
        print("Algorithmic Stock Trading App:")
    # load and validate static data
    stock_history_data_object_list = []
    for symbol in TICKER_SYMBOL_LIST:
        stock_history_object = StockDataHistory(symbol, FIRST_TRADING_DAY, LAST_TRADING_DAY)
        stock_history_object.populate_stock_historical_data()
        stock_history_data_object_list.append(stock_history_object)
    simulation_days = get_static_data_is_valid(stock_history_data_object_list)
    if simulation_days > 0:
        print("all historic stock data valid")
    else:
        print("historic stock data validation failed")
        return
    for stock_history_object in stock_history_data_object_list:
        stock_history_object.populate_technical_analysis_data(simulation_days)

    # initialize starting portfolio
    days_simulated = 0
    portfolio = Portfolio(INITIAL_CASH_BALANCE)
    print('begin trading simulation - portfolio balance: $' + str(INITIAL_CASH_BALANCE))

    # begin simulation
    # TODO: use multithreading for running trade simulations
    eval_obj = tradeeval.TradeEvalObj()

    while days_simulated < simulation_days:

        potential_trades_by_evaluation_score = []
        for stock_history_object in stock_history_data_object_list:
            technical_analysis_dict = stock_history_object.trading_day_object_list[days_simulated].technical_analysis_data
            potential_trades_by_evaluation_score.append([stock_history_object.symbol,
                                                         eval_obj.eval_trade(TRADE_EVAL_STRAT,
                                                                             [technical_analysis_dict])])

        # sell orders - do sales first to maximize potential cash to buy
        portfolio.execute_sell_strategy(potential_trades_by_evaluation_score,
                                        stock_history_data_object_list,
                                        days_simulated)
        portfolio.execute_buy_strategy(potential_trades_by_evaluation_score,
                                       stock_history_data_object_list,
                                       days_simulated)

        days_simulated += 1
    # simulate cash out of all positions
    print("trading simulation complete")
    for trade in portfolio.trade_history:
        print(trade)
    print("S&P 500 strategy trade outcome = $" + str(get_comparison_par(INITIAL_CASH_BALANCE, simulation_days)))
    portfolio_value = 0.0
    for share in portfolio.stock_shares:
        portfolio_value += get_closing_price(stock_history_data_object_list, share.symbol, simulation_days-1)
    print("algorithmic trade portfolio balance = $" + str(portfolio_value + portfolio.cash_balance))
    # TODO: possibly use GUI module to visualize performance

# --- Main App ---
run_back_test(True, False)

