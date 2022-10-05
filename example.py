from lib.main import UonetFSLogin

def example():
    uonet_fslogin = UonetFSLogin(
	username="jan@fakelog.cf", password="jan123", scheme="http", host="fakelog.cf", default_symbol="powiatwulkanowy"
    )
    sessions, user_data = uonet_fslogin.log_in()
    print(sessions, user_data)

if __name__ == "__main__":
    example()
