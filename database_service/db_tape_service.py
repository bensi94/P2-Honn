from sqlalchemy import select, insert, func, and_, update, or_
from shared_utils.logger import _log
from entity_classes.tape import Tape
from entity_classes.user import User
from datetime import datetime, date
from database_service.database_utils import Database_utils
import json

class Database_tape_service:
    
    def __init__(self, connection, tables):
        self.connection = connection
        self.tables = tables
        self.utils = Database_utils(connection)

    # Makes a select * from tables query and returns tapes
    def get_tapes(self):
        select_query = select([self.tables.get_tapes_table()])
        result = self.connection.execute(select_query)

        tapes = []
        for res in result:
            tape = Tape(input_tuple=res)
            tapes.append(tape.return_as_dict())

        return tapes

    # Makes a select * from tables where id == x, query and returns tape
    def get_tape(self, tape_id):
        tape_table = self.tables.get_tapes_table()
        select_query = select([tape_table]).where(tape_table.c.id == tape_id)
        result = self.connection.execute(select_query)
        result = result.fetchone()

        if result is None:
            return None
        else:
            tape = Tape(input_tuple=result)
            return tape.return_as_dict()
    
    # Makes Insert query for tape
    def add_tape(self, tape):
        tape_table = self.tables.get_tapes_table()

        # Checking if eidr exists in database
        if int(self.connection.execute(select(
            [func.count(tape_table.c.eidr)]).where(tape_table.c.eidr 
            == tape['eidr'])).scalar()) > 0:
            response = {
                'code': 400,
                'msg': 'Edir already exists'
            }

        else: 
            insert_query = insert(tape_table).values(
                title=tape['title'],
                director=tape['director'],
                type=tape['type'],
                release_date=tape['release_date'],
                eidr=tape['eidr']
            )

            current_id = self.connection.execute(insert_query).inserted_primary_key[0]
            tape['id'] = current_id

            
            response = {
                'code': 200,
                'msg': json.dumps(tape)
            }
        return response

    # Deletes tape by id
    def delete_tape(self, tape_id):
        tape_table = self.tables.get_tapes_table()

        if self.utils.check_if_exist(tape_table, tape_id) > 0:
            self.delete_borrow(tape_id)
            self.delete_review(tape_id)
            self.connection.execute(tape_table.delete().where(tape_table.c.id == tape_id))
            response = {
                'code': 200,
                'msg': 'Tape with ID:' + str(tape_id) + ' deleted'
            }
        else:
            response = {
                'code': 400,
                'msg': 'Tape ID does not exist'
            }
        return response
    
    # Updates tape at a spesific id
    def update_tape(self, tape_id, tape):
        tape_table = self.tables.get_tapes_table()

        if self.utils.check_if_exist(tape_table, tape_id) > 0:
            if int(self.connection.execute(select(
                [func.count(tape_table.c.eidr)]).where(
                    tape_table.c.eidr == tape['eidr'])).scalar()) > 0:
                response = {
                    'code': 400,
                    'msg': 'Edir already exists'
                }
                return response

            update_query = update(tape_table).values(
                title=tape['title'],
                director=tape['director'],
                type=tape['type'],
                release_date=tape['release_date'],
                eidr=tape['eidr']
            ).where(tape_table.c.id == tape_id)
            self.connection.execute(update_query)
            
            tape['id'] = tape_id

            response = {
                'code': 200,
                'msg': json.dumps(tape)
            }
            return response
        else:
            response = {
                'code': 400,
                'msg': 'Tape ID does not exist'
            }
            return response



    # Delete tapes from borrows, if user_id is set 
    # it only deletes as single tape, otherwise all
    def delete_borrow(self, tape_id, user_id=None):
        borrow_table = self.tables.get_borrow_table()
        
        # Delete all borrows of tape
        if user_id is None:
            self.connection.execute(borrow_table.delete().where(
                borrow_table.c.tape_id == tape_id))
        # Delete borrow of tape by single user
        else:
             self.connection.execute(borrow_table.delete().where(and_(
                 borrow_table.c.tape_id == tape_id, borrow_table.c.user_id == user_id)))

    # Delete tapes from reveiws, if user_id is set
    # it only deletes as single review, otherwise all
    def delete_review(self, tape_id, user_id=None):
        review_table = self.tables.get_review_table()

        # Delete all reviews of tape
        if user_id is None:
            self.connection.execute(review_table.delete().where(
                review_table.c.tape_id == tape_id))
        # Delete review of tape by single user
        else:
             self.connection.execute(review_table.delete().where(and_(
                 review_table.c.tape_id == tape_id, review_table.c.user_id == user_id)))

    
    def register_tape(self, borrow):
        tape_table = self.tables.get_tapes_table()
        user_table = self.tables.get_tapes_table()
        borrow_table = self.tables.get_borrow_table()

        # Checking if user_id and tape_id both exist
        if self.utils.check_if_borrow_exists(borrow_table, borrow['user_id'], borrow['tape_id']):
            response = {
                'code': 400,
                'msg': 'This user already has this tape or loan or has rented it before.'
            }
            return response
        if not self.utils.check_if_exist(tape_table, borrow['tape_id']):
            response = {
                'code': 400,
                'msg': 'No tape with that ID exists'
            }
            return response
        elif not self.utils.check_if_exist(user_table, borrow['user_id']):
            response = {
                'code': 400,
                'msg': 'No user with that ID exists'
            }
            return response

        else: 
            insert_query = insert(borrow_table).values(
                tape_id=borrow['tape_id'],
                user_id=borrow['user_id'],
                borrow_date = borrow['borrow_date'],
                return_date = None
            )

            result = self.connection.execute(insert_query)

            borrow['id'] = result.inserted_primary_key[0]
            
            response = {
                'code': 200,
                'msg': json.dumps(borrow)
            }
            return response

    # Changes return datae from null to the given return_date
    def return_tape(self, return_date, user_id, tape_id):
        borrow_table = self.tables.get_borrow_table()

        if  not self.utils.check_if_borrow_exists(borrow_table, user_id, tape_id):
            response = {
                'code': 400,
                'msg': 'The user with this ID does not have tape on loan with this ID.'
            }
            return response
        else:
            if not self.utils.return_date_is_none(borrow_table, user_id, tape_id):
                response = {
                    'code': 400,
                    'msg': 'Tape has already been returned.'
                }
                return response
            response = {
                'code': 200,
                'msg': 'Tape has been returned'
            }
            update_query = update(borrow_table).values(
                return_date = return_date
            ).where(and_(borrow_table.c.tape_id == tape_id, 
                borrow_table.c.user_id == user_id))
            self.connection.execute(update_query)

            return response

    # Changes return and borrow dates of tape
    def update_registration(self, borrow):
        borrow_table = self.tables.get_borrow_table()
        if self.utils.check_if_borrow_exists(borrow_table, borrow['user_id'], borrow['tape_id']):
            update_query = update(borrow_table).values(
                borrow_date=borrow['borrow_date'],
                return_date=borrow['return_date']
            ).where(and_(borrow_table.c.tape_id == borrow['tape_id'], borrow_table.c.user_id == borrow['user_id']))
            self.connection.execute(update_query)
            response = {
                'code': 200,
                'msg': 'Registration has been updated.'
            }
            return response
        else:
            response = {
                'code': 400,
                'msg': 'This registration does not exist.'
            }
            return response

    def get_tapes_of_user(self, user_id):
        borrow_table = self.tables.get_borrow_table()
        tape_table = self.tables.get_tapes_table()
        user_table = self.tables.get_users_table()

        select_user = select([user_table]).where(user_table.c.id == user_id)
        user_result = self.connection.execute(select_user)
        user_result = user_result.fetchone()
        if user_result == None:
            response = {
                'code': 400,
                'msg': 'There is no user with this ID.'
            }
            return response
        select_query = select(['*']).select_from(tape_table.join(borrow_table)).where(
            and_(borrow_table.c.return_date == None, borrow_table.c.user_id == user_id))

        result = self.connection.execute(select_query)

        # Returns all the tapes from the sql result
        tapes = []
        for res in result:
            tape = Tape(input_tuple=res)
            tapes.append(tape.return_as_dict())

        return tapes
        
    def get_all_reviews(self):
        tapes_table = self.tables.get_tapes_table()
        review_table = self.tables.get_review_table()

        get_query = select(['*']).select_from(tapes_table.join(review_table))
        result = self.connection.execute(get_query)

        # Returns all the tapes from the sql result
        results = []
        for res in result:
            tape = Tape(input_tuple=res)
            return_dict = tape.return_as_dict()
            return_dict['rating'] = res[-1]
            results.append(return_dict)
        return results

    def get_tape_reviews(self, tape_id):
        tapes_table = self.tables.get_tapes_table()
        review_table = self.tables.get_review_table()

        get_query = select(['*']).select_from(
            tapes_table.join(review_table)).where(
                tapes_table.c.id == tape_id)

        result = self.connection.execute(get_query)

        # Returns all the tapes from the sql result
        results = []
        for res in result:
            tape = Tape(input_tuple=res)
            return_dict = tape.return_as_dict()
            return_dict['rating'] = res[-1]
            results.append(return_dict)
        return results
        

    def get_review(self, tape_id, user_id):
        users_table = self.tables.get_users_table()
        tapes_table = self.tables.get_tapes_table()
        review_table = self.tables.get_review_table()

        user_query = select(['*']).select_from(users_table).where(
            users_table.c.id == user_id
        )

        user_res = self.connection.execute(user_query)

        user_res = user_res.fetchone()
        
        if user_res is None:
            return None
        
        user = User(input_tuple=user_res)

        result_dict = user.return_as_dict()

        get_query = select(['*']).select_from(
            tapes_table.join(review_table)).where(and_(review_table.c.user_id
             == user_id, review_table.c.tape_id == tape_id))
        
        result = self.connection.execute(get_query)
        result = result.fetchone()

        # Returns all the tapes from the sql result
        if result is None:
            result_dict['Review'] = 'No review for this tape for this user'
        else:
            tape = Tape(input_tuple=result)
            review_dict = tape.return_as_dict()
            review_dict['rating'] = result[-1]
            result_dict['Review'] = review_dict
        return result_dict

    def on_loan_at(self, loan_date):
        borrow_table = self.tables.get_borrow_table()
        tape_table = self.tables.get_tapes_table()

        select_query = select(['*']).select_from(tape_table.join(borrow_table)).where(
            and_(borrow_table.c.borrow_date <= loan_date, or_(borrow_table.c.return_date > loan_date, borrow_table.c.return_date == None)))
        
        loan_res = self.connection.execute(select_query)

        tapes = []
        for res in loan_res:
            tape = Tape(input_tuple=res)
            tapes.append(tape.return_as_dict())
        tapes = [dict(t) for t in {tuple(d.items()) for d in tapes}]
        return tapes
    
    def on_loan_for(self, loan_duration):
        today = datetime.today().strftime('%Y-%m-%d')
        dur_res = self.connection.execute('SELECT * FROM tapes JOIN borrows ON tapes.id = borrows.tape_id WHERE borrows.return_date IS NULL AND (borrows.borrow_date + \' '+ str(loan_duration) + ' day\'::interval) < \'' + str(today) +'\'')

        tapes = []
        for res in dur_res:
            tape = Tape(input_tuple=res)
            tapes.append(tape.return_as_dict())
        tapes = [dict(t) for t in {tuple(d.items()) for d in tapes}]
        return tapes
    
    def on_loan_for_and_at(self, loan_date, loan_duration):
        query = 'SELECT * FROM tapes JOIN borrows ON tapes.id = borrows.tape_id WHERE (borrows.borrow_date + \''+ str(loan_duration) + 'day\'::interval) < \''+ str(loan_date)+'\'AND (borrows.return_date > \''+str(loan_date)+'\' OR borrows.return_date IS NULL)'
        _log.info(query)
        loan_res = self.connection.execute(query)

        tapes = []
        for res in loan_res:
            tape = Tape(input_tuple=res)
            tapes.append(tape.return_as_dict())
        tapes = [dict(t) for t in {tuple(d.items()) for d in tapes}]
        return tapes

        
