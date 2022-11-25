from uonet_fslogin.main import UonetFSLogin
import asyncio

async def example():
    uonet_fslogin = UonetFSLogin(scheme="https", host="fakelog.cf")
    sessions, user_data = await uonet_fslogin.log_in(username="jan@fakelog.cf", password="jan123", default_symbol="powiatwulkanowy")
    await uonet_fslogin.close()
    print(sessions, user_data)

if __name__ == "__main__":
    asyncio.run(example())
