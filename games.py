from dataclasses import dataclass, field
from enum import Enum
import time
import random

class RPS(Enum):
    ROCK="سنگ"; PAPER="کاغذ"; SCISSORS="قیچی"
WIN={RPS.ROCK:RPS.SCISSORS,RPS.SCISSORS:RPS.PAPER,RPS.PAPER:RPS.ROCK}

@dataclass
class RPSGame:
    chat_id:int; creator:int; opponent:int|None=None; choices:dict[int,RPS]=field(default_factory=dict); created:float=field(default_factory=time.time)
    def expired(self, seconds=300): return time.time()-self.created>seconds
    def choose(self,user,choice):
        if user not in (self.creator,self.opponent): return False,"not_player"
        if user in self.choices: return False,"already"
        self.choices[user]=choice
        if len(self.choices)<2:return True,"waiting"
        a,b=self.creator,self.opponent; ca,cb=self.choices[a],self.choices[b]
        if ca==cb:return True,"draw"
        return True,("creator" if WIN[ca]==cb else "opponent")

@dataclass
class TruthDareGame:
    chat_id:int; players:list[int]; index:int=0; category_id:int|None=None; active:bool=True
    @property
    def current(self): return self.players[self.index] if self.players else None
    def next(self):
        if not self.players:return None
        self.index=(self.index+1)%len(self.players); return self.current
    def remove(self,user):
        if user not in self.players:return
        pos=self.players.index(user); self.players.remove(user)
        if not self.players:self.active=False; self.index=0; return
        if pos<self.index:self.index-=1
        self.index%=len(self.players)

def level(points):
    if points<0:return 1
    return points//100+1
