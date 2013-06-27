import db

session = db.Session()
session.add_all([
    db.Sprinkler(name='backyard-south-grass',           port='A', pin=1, description='Along the fence in the backyard, shoot towards deck'),
    db.Sprinkler(name='backyard-west-grass',            port='A', pin=2, description='Along the west fence'),
    db.Sprinkler(name='backyard-east-grass',            port='A', pin=3, description='Nnear backyard kitchen and firepit'),
    db.Sprinkler(name='front-parking-strip',            port='B', pin=0, description='In the parking strips'),
    db.Sprinkler(name='front-east-grass',               port='B', pin=1, description='Along the east side of the house'),
    db.Sprinkler(name='front-center-grass',             port='B', pin=2, description='First set in just center of the lawn'),
    db.Sprinkler(name='front-center-and-west-grass',    port='B', pin=3, description='Set in the center and around west side of house'),
    db.Sprinkler(name='front-flower-garden',            port='B', pin=4, description='Front flower garden'),
])
session.commit()
print("done")
