from lib.main import UonetFSLogin
import asyncio

async def example():
    uonet_fslogin = UonetFSLogin(
	    username="jan@fakelog.cf", password="jan123", scheme="http", host="fakelog.cf", default_symbol="powiatwulkanowy"
    )
    sessions, user_data = await uonet_fslogin.log_in()
    await uonet_fslogin.close()
    print(sessions, user_data)

if __name__ == "__main__":
    asyncio.run(example())
