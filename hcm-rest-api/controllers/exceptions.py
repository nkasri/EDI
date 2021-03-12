# We treat the exceptions in the parser fonctions for code optimisation and readability

class QueryFormatError(Exception):
    """Invalid Query Format."""