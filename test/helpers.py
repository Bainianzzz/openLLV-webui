from contextlib import contextmanager


@contextmanager
def database_session(factory):
    session = factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()
