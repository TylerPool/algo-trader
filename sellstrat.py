"""
sell strat module
"""


def get_sell_order(strategy_name, trade_evaluation_scores):
    # for now, return buy order as simple dict with symbols for keys and qty to purchase as values
    sell_order = {}
    if strategy_name == "lowscore":
        # for now, trade score is nested list, list of symbol,score lists
        low_score = 0.0
        score_symbol = ""
        for score in trade_evaluation_scores:
            if score[1] < low_score:
                low_score = score[1]
                score_symbol = score[0]
        # choose to buy shares in the highest eval score name, try and by n shares for now (n is arbitrary)
        if score_symbol != "":
            n_shares = 2
            sell_order[score_symbol] = n_shares
    return sell_order
