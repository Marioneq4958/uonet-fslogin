from lib.main import UonetFSLogin

def example():
    # https://github.com/wulkanowy/fake-log/issues/53
    uonet_fslogin = UonetFSLogin(
	username="jan@fakelog.cf", password="jan123", scheme="", symbols=[], host="fakelog.cf"
    )
    sessions, user_data = uonet_fslogin.log_in()
    print(sessions, user_data)

if __name__ == "__main__":
    example()