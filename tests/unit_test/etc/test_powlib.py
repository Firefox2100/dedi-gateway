from dedi_gateway.etc.powlib import PowDriver


class TestPowDriver:
    def test_solve(self):
        nonce = 'dfe041b4f60cb54d082e542b109e392a'
        difficulty = 22

        driver = PowDriver()
        solution = driver.solve(nonce, difficulty)

        assert solution == 9642966

    def test_validate(self):
        nonce = 'dfe041b4f60cb54d082e542b109e392a'
        difficulty = 22
        response = 9642966

        driver = PowDriver()
        is_valid = driver.validate(nonce, difficulty, response)

        assert is_valid is True
