from car_simulator import ManualCar, Engine

m = ManualCar()
m.start_car()
m.clutch_in()
m.shift("1")
m.clutch_out()
try:
    [m.accelerate() for x in range(200)]
except Engine.EngineRedlineError:
    print("Shifting Now!")

m.clutch_in()
m.shift("2")
m.clutch_out()

try:
    [m.accelerate() for x in range(200)]
except Engine.EngineRedlineError:
    print("Shifting Now!")
