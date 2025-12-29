__author__ = 'Maayan'



def check_make_formula(formula):
    formula = formula.replace(" ", "").lower()
    if formula.count("x") == 0:
        raise TypeError("Incorrect format, you need to have at lest one x")
    count_open = 0
    f = 0
    while f < len(formula):
        if not formula[f].isdigit() or formula[f] not in "x()-+%*/":
            raise TypeError("Incorrect format, have invalid chars.")
        if formula[f] == "(": count_open += 1
        elif formula[f] == ")" and count_open == 0:
            raise TypeError("Incorrect format, you have more ) then (")
        elif formula[f] == ")": count_open -= 1
        if f != 0 and formula[f] == "(" and formula[f-1] == ".":
            raise TypeError("Incorrect format, you have dot in before parentheses")
        if f != 0 and formula[f] == "(" and formula[f-1] not in "*/-+%(":
            formula = formula[:f] + "*(" + formula[f+1:]
            f += 1
        f += 1
    if count_open != 0:
        raise TypeError("Incorrect format, you don't close all the parentheses")
    if formula[-1] in "*/%(.":
        raise TypeError("Incorrect format, the format is not finished.")

    return True, formula

def main():
    formula = input("Enter formula (x is the param): ")
    x = 5
    check_make_formula(formula, x)


if __name__ == "__main__":
    main()
