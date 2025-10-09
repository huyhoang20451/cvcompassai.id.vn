from sqlmodel import create_engine, SQLModel, Session

MYSQL_USER = "another"
MYSQL_PASSWORD = "17022004"
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DB = "recruitment_db"

DATABASE_URL = f"mysql+mysqldb://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

engine = create_engine(DATABASE_URL, echo=True)

# Hàm khởi tạo DB (tạo bảng)
def init_db():
    # Import toàn bộ models trước khi tạo bảng
    import models
    SQLModel.metadata.create_all(engine) # Kiểm tra và tạo bảng nếu bảng chưa tồn tại trong metadata

# Dependency để lấy session trong FastAPI
def get_session():
    with Session(engine) as session:
        yield session