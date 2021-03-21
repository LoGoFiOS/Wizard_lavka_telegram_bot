class Repo:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ${num + 1}" for num, item in enumerate(parameters)
        ])
        return sql, tuple(parameters.values())

    async def add_user(self, id: int, ref_code: str, id_who_invited: int, ref_code_amount: int = 3,
                       balance: int = 0) -> None:
        await self.conn.execute(
            "INSERT INTO Users(id, balance, ref_code, id_who_invited, ref_code_amount) "
            "VALUES($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING",
            id, balance, ref_code, id_who_invited, ref_code_amount)

    async def get_user(self, **kwargs):
        # SQL_EXAMPLE = "SELECT * FROM Users where id=1 AND Name='John'"
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.conn.fetchrow(sql, *parameters)

    async def check_ref(self, ref: str):
        sql = "SELECT * FROM users WHERE ref_code=$1 AND ref_code_amount > 0"
        return await self.conn.fetchrow(sql, ref)

    async def add_coins_ref(self, id_who_invited: int, amount: int = 10):
        sql = "UPDATE users SET balance=balance+$1 where id=$2"
        await self.conn.execute(sql, amount, id_who_invited)

    async def change_balance(self, id: int, amount: int):
        sql = "UPDATE users SET balance=$1 where id=$2"
        await self.conn.execute(sql, amount, id)

    async def show_all_items(self):
        return await self.conn.fetch(
            "SELECT * FROM Items ORDER BY name"
        )

    async def add_item(self, name: str, price: int, description: str, img_link: str):
        await self.conn.execute(
            "INSERT INTO Items(name, price, description, img_link) "
            "VALUES($1, $2, $3, $4) ON CONFLICT DO NOTHING",
            name, price, description, img_link)

    async def get_item(self, id: int):
        sql = "SELECT * FROM items WHERE id=$1"
        return await self.conn.fetchrow(sql, id)

    async def get_items(self, text: str):
        txt = "%" + text + "%"
        # sql = "SELECT * FROM Items WHERE LOWER(CONCAT(name, description)) like LOWER($1) ORDER BY name"
        sql = 'SELECT * FROM Items WHERE CONCAT(name, description) ILIKE $1 ORDER BY name'
        return await self.conn.fetch(sql, txt)

    async def add_bill(self, billid: str, status: str = "WAITING"):
        await self.conn.execute(
            "INSERT INTO Bills(billid, status) VALUES($1, $2) ON CONFLICT DO NOTHING",
            billid, status)

    async def update_bill_paid(self, billid: str, status: str = "PAID"):
        sql = "UPDATE Bills SET status=$1 where billid=$2"
        await self.conn.execute(sql, status, billid)
