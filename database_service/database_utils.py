from sqlalchemy import select, func, and_, exists

class Database_utils:

    def __init__(self, connection):
        self.connection = connection
    
    # Counts rows in given table
    def count_rows(self, table):
        return int(self.connection.execute(select([func.count()]).select_from(table)).scalar())

    # Check if id exsits in any given table
    def check_if_exist(self, table, id):
        select_query = select([func.count(table.c.id)]).where(
            table.c.id == id)
        return int(self.connection.execute(select_query).scalar())
    
    def check_if_borrow_exists(self, borrow_table, user_id, tape_id):
        select_query = select([borrow_table]).where(
            and_(borrow_table.c.tape_id == tape_id , borrow_table.c.user_id == user_id))
        result = self.connection.execute(select_query)
        result = result.fetchone()

        if result == None:
            return False

        return True
    
    # Checks if tape is still on rent
    def return_date_is_none(self, borrow_table, user_id, tape_id):
        select_query = select([borrow_table]).where(
            and_(borrow_table.c.tape_id == tape_id , borrow_table.c.user_id == user_id, borrow_table.c.return_date == None))
        result = self.connection.execute(select_query)
        result = result.fetchone()

        if result == None:
            return False

        return True