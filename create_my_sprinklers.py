import db

session = db.Session()

backyard_pots           = db.Sprinkler(name='backyard-pots',                  port='A', pin=0, description='Lines for all the pots on the deck')
backyard_south_grass    = db.Sprinkler(name='backyard-south-grass',           port='A', pin=1, description='Along the fence in the backyard, shoot towards deck')
backyard_west_grass     = db.Sprinkler(name='backyard-west-grass',            port='A', pin=2, description='Along the west fence')
backyard_east_grass     = db.Sprinkler(name='backyard-east-grass',            port='A', pin=3, description='Nnear backyard kitchen and firepit')
front_parking_strip     = db.Sprinkler(name='front-parking-strip',            port='B', pin=0, description='In the parking strips')
front_east_grass        = db.Sprinkler(name='front-east-grass',               port='B', pin=1, description='Along the east side of the house')
front_center_grass      = db.Sprinkler(name='front-center-grass',             port='B', pin=2, description='First set in just center of the lawn')
front_center_and_west   = db.Sprinkler(name='front-center-and-west-grass',    port='B', pin=3, description='Set in the center and around west side of house')
front_flower_garden     = db.Sprinkler(name='front-flower-garden',            port='B', pin=4, description='Front flower garden')

default = db.Schedule(name='default')
schedule_entries = [
    db.ScheduleEntry(index=0, group=0, schedule=default, sprinkler=backyard_south_grass),
    db.ScheduleEntry(index=1, group=0, schedule=default, sprinkler=backyard_west_grass),
    db.ScheduleEntry(index=2, group=0, schedule=default, sprinkler=backyard_east_grass),
    db.ScheduleEntry(index=0, group=1, schedule=default, sprinkler=front_parking_strip),
    db.ScheduleEntry(index=1, group=1, schedule=default, sprinkler=front_east_grass),
    db.ScheduleEntry(index=2, group=1, schedule=default, sprinkler=front_center_grass),
    db.ScheduleEntry(index=3, group=1, schedule=default, sprinkler=front_center_and_west),
    db.ScheduleEntry(index=4, group=1, schedule=default, sprinkler=front_flower_garden),
]
session.add_all([
    backyard_south_grass,
    backyard_west_grass,
    backyard_east_grass,
    front_parking_strip,
    front_east_grass,
    front_center_grass,
    front_center_and_west,
    front_flower_garden,
    default,
] + schedule_entries)
    
session.commit()
print("done")
