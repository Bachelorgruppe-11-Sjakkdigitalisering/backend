from sqlmodel import SQLModel, create_engine, Session

# create sqlite engine
# creates a file named "chess_archive.db"
sqlite_file_name = "chess_archive.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# the engine bridges python and sqlite file
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
  '''
  Helper function to create the tables of the database
  '''
  SQLModel.metadata.create_all(engine)

def get_session():
  '''
  Helper function to get a database session
  '''
  with Session(engine) as session:
    yield session