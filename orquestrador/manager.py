from sqlalchemy import create_engine
from db.models import (Base, Switch, Flow)
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///sqlalchemy_example.db')

Base.metadata.create_all(engine)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

new_switch = Switch(dpid='00000102')
flow1 = Flow(match="in_port=2", action="output=NORMAL", switch=new_switch)
flow2 = Flow(match="in_port=2", action="output=NORMAL", switch=new_switch)

session.add(new_switch)
session.add(flow1)
session.add(flow2)

session.commit()

for flow in new_switch.flows:
    print(flow.__dict__)
