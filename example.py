from lib.main import FSLogin

def example():
    fslogin = FSLogin(scheme="http", symbol="powiatwulkanowy", host="fakelog.cf")
    sessions = fslogin.login(username="jan@fakelog.cf", password="jan123")
    print(sessions)
    fslogin.log_out(session_cookies=sessions["powiatwulkanowy"], symbol="powiatwulkanowy")

if __name__ == "__main__":
    example()