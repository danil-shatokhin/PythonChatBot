import vk
import threading
import re
import requests
import io
import json
import random
from PIL import Image

class ChessCore:
        
    def __init__(self):
        self.board = []
        for i in range(8):
            self.board.append( [ { 'type': 'empty', 'isWhite': False } for i in range(8) ] )
        self.generate_board()
        
        
    def generate_board(self):
        for i in range(8):
            self.board[i][1] = {'type': 'pawn', 'isWhite': True}
            self.board[i][6] = {'type': 'pawn', 'isWhite': False}
            
        self.board[0][0] = {'type': 'rook', 'isWhite': True}
        self.board[1][0] = {'type': 'knight', 'isWhite': True}
        self.board[2][0] = {'type': 'bishop', 'isWhite': True}
        self.board[3][0] = {'type': 'queen', 'isWhite': True}
        self.board[4][0] = {'type': 'king', 'isWhite': True}
        self.board[5][0] = {'type': 'bishop', 'isWhite': True}
        self.board[6][0] = {'type': 'knight', 'isWhite': True}
        self.board[7][0] = {'type': 'rook', 'isWhite': True}
        
        self.board[0][7] = {'type': 'rook', 'isWhite': False}
        self.board[1][7] = {'type': 'knight', 'isWhite': False}
        self.board[2][7] = {'type': 'bishop', 'isWhite': False}
        self.board[3][7] = {'type': 'queen', 'isWhite': False}
        self.board[4][7] = {'type': 'king', 'isWhite': False}
        self.board[5][7] = {'type': 'bishop', 'isWhite': False}
        self.board[6][7] = {'type': 'knight', 'isWhite': False}
        self.board[7][7] = {'type': 'rook', 'isWhite': False}
        
    def is_valid_move(self, move):
        rex = re.compile('^[a-h][0-8]-[a-h][0-8]$');
        return rex.match(move)
    
    def make_move(self, move):
        from_ind = (ord(move[0]) - ord('a'), int(move[1])-1)
        to_ind = (ord(move[3]) - ord('a'), int(move[4])-1)
        
        if self.board[from_ind[0]][from_ind[1]]['type'] == 'empty':
            return "No figure there"
            
        if self.board[to_ind[0]][to_ind[1]]['type'] != 'empty' and \
           self.board[to_ind[0]][to_ind[1]]['isWhite'] == self.board[from_ind[0]][from_ind[1]]['isWhite']:
            return "Can\'t go there"
            
        self.board[to_ind[0]][to_ind[1]] = self.board[from_ind[0]][from_ind[1]]
        self.board[from_ind[0]][from_ind[1]] = {'type': 'empty', 'isWhite': True}
        
        return ""
        
    def generate_image(self):
        black_cell = Image.open( "chess_images/black_cell.png" )
        white_cell = Image.open( "chess_images/white_cell.png" )
        res = Image.new("RGB", (60*8, 60*8), "white")
        
        for i in range(8):
            for j in range(8):
                if (i+j)%2 == 1:
                    res.paste( black_cell, (60*i, 60*j) )
                else:
                    res.paste( white_cell, (60*i, 60*j) )
                    
                if self.board[i][j]['type'] != 'empty':
                    figure_path = 'chess_images/'
                    if self.board[i][j]['isWhite']:
                        figure_path += 'white_'
                    else:
                        figure_path += 'black_'
                    figure_path += self.board[i][j]['type'] + '.png'
                    
                    figure_image = Image.open( figure_path )
                    print 'drawing ' + str(self.board[i][j]) + ' at ' + str(60*i) + ' ' + str(60*j)
                    res.paste( figure_image, (60*i, 60*j), figure_image )
                    
        return res
            
        
class VKWrap:    
    def __init__(self): 
        try:
            with open( 'mid', 'r' ) as f:
                self.last_message_id = int(f.read())
        except:
            self.last_message_id = 0
        
        self.USER_ID = '252410971'
        self.TOKEN = '887c1f1090c79f30156816b9c6bd0675230443b1fac2d7e7cd8edf147cb612cf7acbfb4bd1bf1b94b601b'
        self.CHAT_ID = 2
        self.session = vk.Session()
        self.api = vk.API(self.session)
    
    
    def check_messages(self):
        command_list = []
        messages = self.api.messages.get( chat_id = self.CHAT_ID, last_message_id = self.last_message_id, access_token = self.TOKEN )
        for message in messages[1:]:
            if message['mid'] < self.last_message_id:
                break

            command_list.append( { "author": message["uid"], "text": message["body"] } )
        
            if int(messages[1]['mid']) > self.last_message_id:           
                self.last_message_id = int(messages[1]['mid'])
                try:
                    with open( 'mid', 'w' ) as f:
                        f.write( str(self.last_message_id) )
                except:
                    pass
                
        return command_list
        
        
    def send_message(self, message_text):
        self.api.messages.send( chat_id = self.CHAT_ID, message = message_text, access_token = self.TOKEN )
    
    def send_image(self, image):
        method_url = 'https://api.vk.com/method/photos.getMessagesUploadServer?'
        data = dict(access_token=self.TOKEN)
        response = requests.post(method_url, data)
        result = json.loads(response.text)
        upload_url = result['response']['upload_url']

        byteIO = io.BytesIO()
        image.save( byteIO, format='PNG' )
        image_bytes = byteIO.getvalue()
        
        img = {'photo': ('board.png', image_bytes) }
        response = requests.post(upload_url, files=img)
        result = json.loads(response.text)
        #print result

        method_url = 'https://api.vk.com/method/photos.saveMessagesPhoto?'
        data = dict(access_token=self.TOKEN, photo=result['photo'], hash=result['hash'], server=result['server'])
        response = requests.post(method_url, data)
        result = json.loads(response.text)['response'][0]['id']
        
        self.api.messages.send( chat_id = self.CHAT_ID, attachment = result, access_token = self.TOKEN )
        

class BotController: 
    #TODO: confirmation on restart
    #TODO: turning move back
    def __init__(self):
        self.vk_wrap = VKWrap()
        self.game_core = ChessCore()
        self.confirmation_await = False
        
        self.AVAILABLE_COMMANDS = { ']]roll': 'self.vk_wrap.send_message(str(random.randint(1,12)))',
                                    ']]bark': "self.vk_wrap.send_message('woof woof')",
                                    ']]restart': 'self.restart()',
                                    ']]help': 'self.vk_wrap.send_message(str( self.AVAILABLE_COMMANDS.keys() ))',
                                    ']]board': 'self.vk_wrap.send_image( self.game_core.generate_image() )' }
        
        
        threading.Timer(2, self.check_messages).start()
        
    def check_messages(self):
        command_list = self.vk_wrap.check_messages()
        for command in reversed(command_list):
            if command['text'].startswith(']]'):
                self.execute(command)
            elif self.game_core.is_valid_move(command['text']):
                response = self.game_core.make_move( command['text'] )
                if response:
                    self.vk_wrap.send_message( response )
                else:
                    self.vk_wrap.send_image( self.game_core.generate_image() )
                
        threading.Timer(4, self.check_messages).start()
                
    
    
    def execute(self, command):
        if command['text'] in self.AVAILABLE_COMMANDS.keys():
            eval( self.AVAILABLE_COMMANDS[command['text']] )
        else:
            self.vk_wrap.send_message( '[CORE] Unknown command' )
        
    def restart(self):
        self.game_core = ChessCore()
        

controller = BotController()

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        