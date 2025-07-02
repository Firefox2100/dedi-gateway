from dedi_gateway.etc.powlib import solve, validate


class TestPowLib:
    def test_solve(self):
        nonce = 'dfe041b4f60cb54d082e542b109e392a'
        difficulty = 22

        solution = solve(nonce, difficulty)

        assert solution == 9642966

    def test_validate(self):
        nonce = 'dfe041b4f60cb54d082e542b109e392a'
        difficulty = 22
        response = 9642966

        is_valid = validate(nonce, difficulty, response)

        assert is_valid is True
