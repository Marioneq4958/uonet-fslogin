from lib.main import UonetFSLogin

def example():
    # https://github.com/wulkanowy/fake-log/issues/53
    uonet_fslogin = UonetFSLogin(username="jan@fakelog.cf", password="jan123", scheme="http", symbols=["powiatwulkanowy"], host="fakelog.cf")
    sessions = uonet_fslogin.log_in()
    uonet_fslogin.log_out("powiatwulkanowy", sessions["powiatwulkanowy"])
    print(sessions)

if __name__ == "__main__":
    example()