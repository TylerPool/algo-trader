"""
buy strategy module
"""


def get_buy_order(strategy_name, trade_evaluation_scores):

    # for now, return buy order as simple dict with symbols for keys and qty to purchase as values
    buy_order = {}
    if strategy_name == "highscore":
        # for now, trade score is nested list, list of symbol,score lists
        high_score = 0.0
        high_score_symbol = ""
        for score in trade_evaluation_scores:
            if score[1] > high_score:
                high_score = score[1]
                high_score_symbol = score[0]
        # choose to buy shares in the highest eval score name, try and by n shares for now (n is arbitrary)
        if high_score_symbol != "":
            n_shares = 2
            buy_order[high_score_symbol] = n_shares

    return buy_order
