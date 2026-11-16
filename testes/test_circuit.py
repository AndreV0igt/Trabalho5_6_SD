import pytest
from servico_pedidos.resiliencia import Circuit, Unavailable

def test_open_recovery():
    c = Circuit()
    for _ in range(3):
        c.finish(c.admit(), False)
    assert c.state == "OPEN"
    with pytest.raises(Unavailable):
        c.admit()
    c.opened_at -= 6
    token = c.admit()
    assert c.state == "HALF_OPEN"
    with pytest.raises(Unavailable):
        c.admit()
    c.finish(token, True)
    assert c.state == "CLOSED"

def test_failed_probe():
    c = Circuit(threshold=1)
    c.finish(c.admit(), False)
    c.opened_at -= 6
    c.finish(c.admit(), False)
    assert c.state == "OPEN"

def test_stale_completion():
    c = Circuit(threshold=1)
    old = c.admit()
    c.finish(c.admit(), False)
    c.finish(old, True)
    assert c.state == "OPEN"
