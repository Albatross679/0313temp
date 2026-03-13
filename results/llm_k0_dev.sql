SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.departure_time = DATE_ADD(NOW(), INTERVAL 1 DAY) AND f.from_airport = 'DENV' AND f.to_airport = 'PHL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.arrival_time BETWEEN '14:00:00' AND '17:00:00' AND fs.stop_days = 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time < '9:00:00' AND f.to_airport = 'BALtimore' AND f.day_name = 'Thursday';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PHOENIX' AND fs.arrival_airport = 'MILWAUKEE';
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.stops, f.flight_days, f.connections, f.arrival_airport, f.airline_flight FROM flight f WHERE f.from_airport = 'PHL' AND f.to_airport = 'SFO' AND f.departure_time = '2023-10-27 12:00:00';
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight FROM flight f WHERE f.departure_time = 'Denver';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.departure_airport = 'BOS' AND fs.arrival_airport = 'SFO' AND fl.stop_days = 0;
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight, f.meal_code FROM flight f WHERE f.to_airport = 'DENV' AND f.from_airport = 'ATL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'BAL' AND fs.arrival_airport = 'ATL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'JFK'   AND fs.arrival_airport = 'TAM'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'ATL' AND fs.arrival_airport = 'BAL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'DAL' AND fs.arrival_airport = 'BOS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_date = '2023-10-27'   AND f.from_airport = 'HOUSTON'   AND f.to_airport = 'MILWAUKEE'   AND f.day = 'friday'   AND f.airline_code = 'AA';
SELECT * FROM flight WHERE to_airport = 'BOS' AND airline_code = 'UA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Denver' AND c.city_name = 'Philadelphia';
SELECT f.flight_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'DENV' AND f.arrival_airport = 'BOS' ORDER BY f.departure_time ASC;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_airport = 'SFO' AND f.departure_date = '2023-08-08'
SELECT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.arrival_time FROM flight f WHERE f.to_airport = 'OAKL'   AND f.arrival_time = '17:00:00'   AND f.flight_days = 1;
SELECT flight.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE origin = 'DAL' ORDER BY fare.round_trip_cost LIMIT 1;
SELECT f.flight_id, f.arrival_time FROM flight f WHERE f.from_airport = 'BOS' AND f.arrival_time < '08:00:00'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_number = (     SELECT MAX(stop_number)     FROM flight_stop     WHERE departure_airport = 'BOS'     AND arrival_airport = 'SFO' );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Philadelphia' AND c.country_name = 'United States' AND f.to_airport = 'DALLAS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time = '16:00:00' AND f.from_airport = 'PHL'
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id JOIN fare_basis fb ON ff.fare_basis_code = fb.code WHERE f.from_airport = 'LAX'   AND f.arrival_time = 'MONDAY 08:00'   AND f.flight_days = 1;
SELECT f.*
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time BETWEEN '10:00:00' AND '15:00:00' AND f.from_airport = 'PITTSBURGH' AND f.to_airport = 'FORT_WORTH';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Philadelphia' AND f.departure_airport = 'DAL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 2 AND f.from_airport = 'SFO' AND f.to_airport = 'PIT' AND f.day = 'TUESDAY';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.to_airport = 'ORD'   AND flight.departure_time = '2023-10-27 20:00:00'   AND flight.airline_code = 'UA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston' AND f.to_airport = 'SFO' AND fs.stop_days = 1 AND f.airline_code = 'AA';
SELECT flight_id, departure_time FROM flight WHERE to_airport = 'PHL'   AND departure_time = 'Tuesday 07:00'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PIT' AND fs.arrival_airport = 'PHI';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_time BETWEEN '430' AND '530' AND fs.stop_days >= 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Detroit' AND c.city_name = 'Chicago';
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight, f.meal_code, f.fare_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Baltimore' AND c.city_name = 'Philadelphia';
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.to_airport, f.airline_code FROM flight f WHERE f.from_airport = 'BOS' AND f.to_airport = 'DEN';
SELECT flight_id, departure_time, arrival_time FROM flight WHERE to_airport = 'DAL'   AND departure_time < '2023-10-27 07:00:00'   AND arrival_time > '2023-10-27 17:00:00';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'PHL' AND f.arrival_date = 'SUNDAY'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_time > 5 AND f.from_airport = 'DENV' AND f.to_airport = 'DALS';
SELECT f.fare_id, f.round_trip_cost FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.from_airport = 'BOS' AND f.to_airport = 'DEN' OR f.from_airport = 'BOS' AND f.to_airport = 'DEN'
SELECT * FROM flight WHERE to_airport = 'IND' AND from_airport = 'ORD' AND flight_date = '2023-12-27'
SELECT f.* FROM flight f WHERE f.departure_time > 1600 AND f.flight_id IN (     SELECT flight_id     FROM flight_stop     WHERE departure_time >= 1600     AND stop_days >= 1     AND departure_airline = 'ATL' ) AND f.flight_days >= 1;
SELECT f.flight_id, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.to_airport = 'TOA' AND f.arrival_time BETWEEN '17:00:00' AND '19:00:00'
SELECT aircraft_code FROM flight WHERE departure_time < '10:00:00' AND from_airport = 'DENV' AND aircraft_code_sequence IN (   SELECT aircraft_code   FROM flight   WHERE departure_time < '10:00:00'   AND from_airport = 'DENV' );
SELECT * FROM flight WHERE departure_airport = 'DENV' AND arrival_time = '17:00:00' AND to_airport = 'SFO' AND flight_days = 1;
SELECT f.flight_id, f.arrival_time, f.flight_number, c.city_name FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'DENV' AND c.city_name = 'BALtimore';
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight, f.meal_code, f.fare_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Dallas' AND f.to_airport = 'PIT'
SELECT * FROM ground_service WHERE airport_code = 'PHL' AND date = 'Wednesdays' AND time_zone_code = 'America/New_York';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Orlando' AND c.city_name = 'Kansas City';
The provided context does not contain any information regarding ground transportation in Oakland, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'DENV' AND fs.arrival_airport = 'PHL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco' AND c.city_name = 'Pittsburgh';
SELECT fare.fare_id FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.to_airport = 'JFK'   AND flight.from_airport = 'NYC'   AND fare.round_trip_required = 'YES';
SELECT DISTINCT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.departure_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston' AND c.city_name = 'Denver'
SELECT f.* FROM flight f WHERE f.from_airport = 'SFO' AND f.to_airport = 'PIT'
SELECT * FROM flight WHERE airline_code = 'AA' AND departure_airport = 'BOS' AND arrival_airport = 'DEN';
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.from_airport = 'SFO' AND f.to_airport = 'DEN' AND fb.class_description = 'Business';
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.to_airport = 'DAL'   AND f.departure_time = 'tomorrow'   AND f.flight_id IN (     SELECT flight_id     FROM flight     WHERE to_airport = 'BOS'   );
SELECT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.arrival_time, f.departure_time, f.stops, f.flight_days, f.connections
SELECT DISTINCT a.aircraft_code FROM flight f JOIN aircraft a ON f.aircraft_code = a.aircraft_code WHERE f.to_airport = 'BOS' AND f.from_airport = 'SFO'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston' AND c.city_name = 'Denver'
SELECT flight_id FROM flight WHERE departure_airport = 'BOS'   AND arrival_time = (     SELECT MIN(arrival_time)     FROM flight     WHERE departure_airport = 'BOS'       AND arrival_time >= DATE_ADD(NOW(), INTERVAL 1 DAY)   );
SELECT f.* FROM flight f WHERE departure_time = '13:00:00' AND from_airport = 'CHARLOTTE'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time < '18:00'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days >= 16 AND f.to_airport = 'OAKL' AND f.from_airport = 'DALS'
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.from_airport = 'DAL' AND f.to_airport = 'BAL' AND fb.class_type = 'FIRST CLASS';
SELECT f.* FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.to_airport = 'DAL'   AND f.from_airport = 'DFW'   AND f.restriction_code = 'DELTA'   AND f.round_trip_required = 1;
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'CLE'   AND f.departure_date = '2023-10-23'   AND f.airline_flight = 'UA'
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight FROM flight f WHERE f.to_airport = 'DALLAS' AND f.from_airport = 'PHILADELPHIA';
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 0 AND f.to_airport = 'LASV' AND f.from_airport = 'NYCW' AND f.airline_code = 'ASW';
SELECT * FROM flight WHERE from_airport = 'BOS'   AND to_airport = 'WAW';
The provided text does not contain any information regarding the term "iah", so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time = '20:00:00' AND f.to_airport = 'BALtimore'
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight FROM flight f WHERE f.to_airport = 'PHL' AND f.from_airport = 'DAL';
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.stops, f.flight_days, f.connections FROM flight f WHERE f.to_airport = 'PHL' AND f.departure_date = '2023-10-27' AND f.arrival_date = '2023-10-27' AND f.flight_number = 12345;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Charlotte'
SELECT COUNT(*) FROM flight WHERE to_airport = 'SFO' AND from_airport = 'PHI' AND flight_date = '2023-08-18';
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.to_airport = 'BOS' AND f.from_airport = 'PIT'
SELECT f.flight_id, f.fare_id FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.round_trip_required = 1 ORDER BY f.fare_id DESC;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'LGD' OR f.to_airport = 'JFK' AND f.departure_time BETWEEN '2023-10-27' AND '2023-10-29';
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.to_airport, f.airline_code FROM flight f WHERE f.departure_airport = 'DENV' AND f.arrival_airport = 'PIT';
SELECT flight.flight_id FROM flight WHERE departure_airport = 'ATL' AND arrival_airport = 'BOS' ORDER BY flight.departure_time ASC LIMIT 1;
SELECT f.flight_id, f.departure_time FROM flight f WHERE f.to_airport = 'ATL'   AND f.departure_date = '2023-09-05'   AND f.flight_number = 12345;
SELECT DISTINCT f.airline_code FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_airport = 'JFK' AND f.arrival_day = 'friday'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_airport = 'BOS'   AND f.day = 'WEDNESDAY'   AND f.time = '09:00:00'   AND fs.arrival_airport = 'DEN' ;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.from_airport = 'PIT' AND f.to_airport = 'SFO' AND f.departure_date = '2023-10-27'
SELECT EXISTS(     SELECT 1     FROM airport     WHERE airport_code = 'BOS'     AND EXISTS(         SELECT 1         FROM ground_service         WHERE airport_code = 'BOS'         AND transport_type = 'BUS'     ) ) AS has_ground_transportation_to_downtown;
SELECT flight_id, flight_number, arrival_time FROM flight WHERE departure_airport = 'DAL' AND arrival_time <= '16:00' AND flight_day = 'Sat' AND arrival_airport = 'SFO'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Denver' AND c.city_name = 'San Francisco';
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id JOIN fare_basis fb ON ff.fare_basis_code = fb.code WHERE f.from_airport = 'DAL' AND f.to_airport = 'BOS'
SELECT aircraft_code FROM flight WHERE flight_id = (     SELECT flight_id     FROM flight     WHERE flight_number = '1209' );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_time < '12:00:00' AND f.to_airport = 'DENV' AND c.country_name = 'USA'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'ATL' AND fs.arrival_airport = 'BOS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco' AND c.city_name = 'Boston';
SELECT COUNT(*) FROM flight WHERE to_airport = 'SFO' AND flight_days >= 1;
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time FROM flight f WHERE f.to_airport = 'HOUSTON'   AND f.departure_time = 'TUESDAY'   AND f.arrival_time = 'METHAMPIS';
SELECT flight.flight_id, flight.fare_id FROM flight JOIN fare_basis ON flight.flight_id = fare_basis.flight_id WHERE flight.from_airport = 'ATL' AND flight.to_airport = 'PIT' ORDER BY fare_basis.basis_days;
SELECT ground_service.transport_type, ground_service.city_code FROM ground_service WHERE airport_code = 'PIT' AND class_of_service = 'economy';
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight, f.meal_code, f.fare_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco' AND f.to_airport = 'Pittsburgh';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco' AND f.arrival_time = 'Monday 08:00'
SELECT f.flight_id, f.arrival_time, f.flight_number, c.city_name FROM flight f JOIN city c ON f.from_airport = c.city_name;
SELECT flight_id, aircraft_code FROM flight WHERE departure_time > 17;
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id JOIN fare_basis fb ON ff.fare_basis_code = fb.code WHERE f.to_airport = 'DALLAS'   AND f.from_airport = 'BALtimore';
The provided text does not contain any information regarding the meaning of "ff", so I am unable to extract the requested data from the provided context.
SELECT flight.aircraft_code FROM flight WHERE departure_time < '10:00:00' AND flight.from_airport = 'DENVER' AND flight.to_airport = 'SANFRANCISCO';
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.stops, f.flight_days, f.connections, f.from_airport, f.airline_flight, f.meal_code FROM flight f WHERE f.from_airport = 'PHL' AND f.to_airport = 'DAL';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.from_airport = 'BOS'   AND flight.to_airport = 'SFO'   AND fare.restriction_code = 'FIRSTCLASS';
SELECT flight_id, fare_id FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE from_airport = 'BOS' AND to_airport = 'DEN' ORDER BY fare_id LIMIT 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Baltimore' AND c.city_name = 'San Francisco';
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight, f.meal_code FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Baltimore' AND c.city_name = 'Dallas'
SELECT f.* FROM flight f WHERE f.to_airport = 'ATL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PHL' AND fs.arrival_airport = 'DAL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Seattle' AND c.city_name = 'Salt Lake City';
SELECT flight.flight_id FROM flight WHERE departure_airport = 'PIT' AND arrival_airport = 'SFO' ORDER BY flight.departure_time LIMIT 1;
SELECT * FROM flight WHERE departure_time BETWEEN '12:00:00' AND '17:00:00';
The provided text does not contain any information regarding the SQL query, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time < '19:00:00' AND f.arrival_time >= '14:00:00' AND f.to_airport = 'LAX' AND f.airline_code = 'UA'
The provided context does not contain any information regarding ground transportation in Boston, so I am unable to extract the requested data from the provided context.
SELECT flight_id FROM flight WHERE departure_airport = 'BOS' AND arrival_airport = 'BWI' AND meal_code = 'MEALCODE' AND departure_time = (     SELECT MIN(departure_time)     FROM flight     WHERE departure_airport = 'BOS'     AND arrival_airport = 'BWI'     AND meal_code = 'MEALCODE' );
SELECT COUNT(*) FROM flight WHERE arrival_airport = 'General Mitchell International Airport';
SELECT f.to_airport FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.country_name = 'Canada';
The provided SQL query does not contain any information regarding ground transportation from Pittsburgh Airport to the town, so I am unable to extract the requested data from the provided context.
The provided context does not contain any information regarding the capacity of an F28, so I am unable to extract the requested data from the provided context.
SELECT * FROM flight WHERE departure_date = '2023-10-27'   AND from_airport = 'DENV'   AND saturday_stay_required = 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_time > '12:00:00' AND f.to_airport = 'CLE' AND f.airline_code = 'US';
SELECT * FROM flight WHERE departure_time > '15:00:00' AND to_airport = 'ATL' AND to_airport = 'WAS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'CLE' AND fs.arrival_airport = 'MEM'
The provided context does not contain any information regarding the fare code qw, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'CINcinnati' AND fs.arrival_airport = 'Toronto';
SELECT f.flight_id, f.fare_id, f.flight_number, f.arrival_time, f.time_elapsed FROM flight f JOIN fare f ON f.flight_id = f.flight_id;
SELECT f.* FROM flight f WHERE f.from_airport = 'ATL' AND f.to_airport = 'BOS' ORDER BY f.arrival_time DESC;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'MEMPH' AND fs.arrival_airport = 'LASV';
SELECT flight_id, flight_number, from_airport, airline_name FROM flight WHERE to_airport = 'ATL'   AND departure_time = '2023-10-27 19:00:00'   AND aircraft_code = '757';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN food_service fsf ON f.flight_id = fsf.flight_id WHERE fsf.meal_code = 'SUPPER' AND f.arrival_day = 'friday' AND f.departure_airport = 'STL' AND f.arrival_airport = 'MCI';
SELECT EXISTS(     SELECT 1     FROM airport     WHERE airport_code = 'BOS'     AND EXISTS(         SELECT 1         FROM ground_service         WHERE airport_code = 'BOS'     ) ) AS has_ground_transportation;
SELECT f.to_airport, f.flight_days FROM flight f WHERE f.from_airport = 'BALMD'   AND f.to_airport = 'SFO'   AND f.round_trip_required = 1;
SELECT fare.fare_id FROM fare WHERE to_airport = 'DAL'   AND restriction_code = 'ROUNDTRIP'   AND round_trip_required = 'YES'   AND fare_basis_code = 'economy';
SELECT * FROM flight WHERE departure_airport = 'SEA' AND flight_day = 'SUNDAY' AND departure_time > 1730;
SELECT f.* FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.to_airport = 'PITTSBURGH' AND f.arrival_time > '12:00' AND ff.fare_id < 1100
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston' AND c.city_name = 'Dallas';
SELECT flight_id, fare_id FROM flight WHERE to_airport = 'BALMD' AND departure_time = (     SELECT MAX(departure_time)     FROM flight     WHERE to_airport = 'SFO'     AND departure_time < '2023-10-27' );
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight FROM flight f WHERE f.to_airport = 'AMS'   AND f.departure_date = '2023-10-27'   AND f.flight_days = 1;
SELECT * FROM flight WHERE airline_code = 'XYZ' AND departure_time BETWEEN '12:00:00' AND '14:00:00';
SELECT * FROM flight WHERE departure_time >= '7:00:00' AND from_airport = 'PHL' AND flight_days = 1 AND arrival_time > 0;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Salt Lake City'
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 0 AND f.from_airport = 'NSH' AND f.to_airport = 'STL';
SELECT DISTINCT airline.airline_name FROM airline JOIN flight ON airline.airline_code = flight.airline_code;
SELECT ground_service.transport_type FROM ground_service WHERE airport_code = 'SFO'   AND city_code = 'SANFRANCISCO';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'ATL' AND fs.arrival_airport = 'WAW';
The provided context does not contain any information regarding the SQL query to translate the question, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Dallas' AND c.city_name = 'Baltimore' AND f.airline_code IN ('AMZN', 'DAL');
The provided context does not contain any information regarding the limousine service cost within Pittsburgh, so I am unable to extract the requested data from the provided context.
SELECT flight.fare_id FROM flight JOIN fare_basis ON flight.flight_id = fare_basis.flight_id WHERE flight.from_airport = 'BOS' AND fare_basis.basis_days = 1 ORDER BY fare_basis.fare_id LIMIT 1;
SELECT * FROM flight WHERE departure_day = 'Sunday' AND departure_time = '08:00:00' AND to_airport = 'MIA' AND airline_code = 'EVS';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.to_airport = 'ATL'   AND flight.from_airport = 'SFO';
SELECT flight_id, departure_time, meal_code FROM flight WHERE departure_airport = 'DENV' AND arrival_airport = 'SFO' AND meal_code = 'BREAKFAST';
SELECT * FROM flight WHERE from_airport = 'CLE' AND arrival_time < '16:00' AND airline_code = 'US';
The provided context does not contain any information regarding Lufthansa, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT f.airline_code FROM flight f JOIN airline a ON f.airline_code = a.airline_code WHERE f.from_airport = 'WA' AND f.to_airport = 'DEN'
SELECT f.meal_code FROM flight f JOIN food_service fs ON f.meal_code = fs.meal_code WHERE f.flight_id = 270 AND f.from_airport = 'DENV' AND f.to_airport = 'PHL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN airport a ON fs.arrival_airport = a.airport_code WHERE a.country_name = 'United States' AND f.arrival_time BETWEEN '12:00:00' AND '16:00:00' AND f.airline_code IN ('DAL', 'UA', 'EV', 'NK');
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_date = '2023-10-25'   AND f.to_airport = 'CLE'   AND f.to_airport = 'MIA'
SELECT flight_id, flight_number, arrival_time FROM flight WHERE departure_airport = 'OAKL' AND arrival_time BETWEEN '17:00:00' AND '18:00:00' AND flight_number NOT IN (     SELECT flight_id     FROM flight     WHERE departure_airport = 'OAKL'     AND arrival_time BETWEEN '16:00:00' AND '17:00:00' );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'PHOENIX' AND f.arrival_date = 'WED' AND c.city_name = 'MILWAUKEE';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.departure_time >= '12:00' AND ff.fare_id NOT LIKE '1100%'
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 0 AND f.from_airport = 'DAL' AND f.to_airport = 'HOU';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.arrival_time < '17:00' AND f.from_airport = 'CHI' AND f.to_airport = 'MIL' ORDER BY f.arrival_time DESC;
SELECT f.*
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.from_airport = 'PHL' AND f.arrival_time < '12:00:00' AND f.airline_code = 'AA';
SELECT fare.fare_id FROM flight_fare JOIN fare_basis ON fare.fare_basis_code = fare_basis.farebasiscode WHERE flight_id = 928 AND airline_code = 'AA';
The provided SQL query does not contain any information related to the distance from the airport in the Dallas-Fort Worth Airport, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.from_airport, f.to_airport, f.airline_code FROM flight f WHERE f.departure_time = CURDATE() AND f.to_airport = 'BUR'
SELECT airline_code FROM airline WHERE city_name = 'Washington' AND destination_city = 'San Francisco';
SELECT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.arrival_time, f.departure_time, f.stops, f.flight_days, f.connections FROM flight f WHERE f.to_airport = 'LAS' AND f.from_airport = 'NYC' AND f.round_trip_required = 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'DALLAS'   AND f.from_airport = 'ATL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Phoenix' AND c.city_name = 'Las Vegas';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Chicago' AND f.arrival_day = 'Sunday' AND f.airline_code = 'Continental'
SELECT f.*
SELECT f.* FROM flight f JOIN flight_stop fs ON f.to_airport = fs.stop_airport WHERE fs.stop_airport <> 'Love Field' ORDER BY f.flight_id;
SELECT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.arrival_time, f.departure_time FROM flight f WHERE f.from_airport = 'Love Field'    OR f.to_airport = 'Love Field';
SELECT * FROM flight WHERE to_airport = 'BOS' AND from_airport = 'OAK' AND EXISTS (   SELECT 1   FROM flight_stop   WHERE departure_airline = 'AA'   AND stop_airport = 'DEN' );
SELECT f.flight_number, f.fare_id, f.from_airport, f.arrival_time
The provided SQL query does not contain any information related to ground transportation between the San Francisco Airport and the city, so I am unable to extract the requested data from the provided context.
SELECT * FROM flight WHERE departure_airport = 'ATL' AND arrival_airport = 'DEN';
The provided context does not contain any information regarding ground transportation available in San Francisco, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.from_airport = 'OAKL' AND f.to_airport = 'SFO';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_date = '2023-10-27'   AND fs.stop_days = 2   AND f.arrival_date = '2023-10-30'   AND f.airline_code = 'UA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_date = '1991-07-25' AND f.from_airport = 'DENV' AND f.to_airport = 'BAL' AND f.class_type = 'FIRST CLASS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.airline_code = 'AA' AND c.city_name = 'Phoenix'
SELECT flight.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE origin = 'ATL'   AND destination = 'BWI'   AND roundtrip_required = 'YES' ORDER BY fare.round_trip_cost ASC;
SELECT DISTINCT f.airline_code FROM flight f JOIN airline a ON f.airline_code = a.airline_code WHERE f.from_airport = 'TOR' AND f.to_airport = 'DEN'
SELECT fare_id FROM flight_fare WHERE to_airport = 'SFO'   AND departure_date = '2023-11-07'   AND flight_number = 12345;
The provided text does not contain any information regarding the term "ewr", so I am unable to extract the requested data from the provided context.
SELECT flight_id, flight_number, departure_time FROM flight WHERE from_airport = 'CHI'   AND airline_code = 'CAL'   AND departure_time < '07:00:00';
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight, f.meal_code, f.fare_id
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.from_airport = 'PHL' AND f.to_airport = 'DAL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time = '00:00:00' AND f.to_airport = 'PITTSBURGH' AND f.airline_code = 'OOAK'
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.to_airport = 'DENV'   AND flight.from_airport = 'SFO'   AND flight.restriction_code = 'UA297';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PHL'   AND fs.arrival_airport = 'SFO';
SELECT f.flight_id, f.arrival_time, f.flight_number, c.city_name FROM flight f JOIN city c ON f.from_airport = c.city_name WHERE f.flight_id = (     SELECT flight_id     FROM flight     WHERE to_airport = 'ATL'       AND departure_date = '2023-10-27'       AND flight_number = 12345 );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_time < '10:00:00'
SELECT f.to_airport, f.flight_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.to_airport = 'PHL' AND fs.stop_airport = 'DAL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'KCLT'   AND f.departure_date = '2023-10-27'   AND f.flight_number = 12345;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time BETWEEN '08:00:00' AND '12:00:00' AND f.from_airport = 'PHL' AND f.to_airport = 'BAL';
SELECT DISTINCT c.city_name FROM city c JOIN flight f ON c.city_code = f.from_airport WHERE f.airline_code = 'CAN';
SELECT * FROM flight WHERE from_airport = 'BAL' OR to_airport = 'BAL';
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_code
SELECT f.* FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id JOIN fare_basis fb ON ff.fare_basis_code = fb.code WHERE f.departure_time >= '19:00:00' AND f.application = 'economy' AND f.to_airport = 'BWX'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Atlanta' AND f.to_airport = 'BOS'
SELECT f.flight_id, f.flight_number, f.from_airport, f.airline_code, f.departure_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.from_airport = 'CINcinnati' AND f.destination_airport = 'HOUSTON';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Denver' AND c.city_name = 'San Francisco' OR c.city_name = 'Philadelphia';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'New York' AND c.city_name = 'Miami';
SELECT DISTINCT f.airline_code FROM flight f JOIN flight_leg fl ON f.flight_id = fl.flight_id JOIN airport a ON fl.from_airport = a.airport_code JOIN airport b ON fl.to_airport = b.airport_code WHERE a.city_name = 'Pittsburgh' AND b.city_name = 'Baltimore';
The provided text does not contain any information regarding "sa", so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.departure_airport = 'BWI'   AND fs.arrival_airport = 'DEN'   AND fl.leg_flight = 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_time < '0900' AND f.to_airport = 'ATL' AND fs.stop_days = 1 AND f.airline_code = 'UA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.country_name = 'United States' AND f.from_airport = 'JFK' AND f.to_airport = 'BNA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.day_name = 'Monday' AND f.to_airport = 'BALMD' AND f.to_airport = 'DALAS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'BOS' AND f.departure_date = '2023-11-11'
The provided context does not contain any information regarding ground transportation between Orlando International and Orlando, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.departure_airport, f.arrival_airport, f.flight_days, f.connections, f.arrival_time, f.time_elapsed FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Chicago' AND c.country_name = 'USA' AND f.arrival_airport = 'SFO' AND f.flight_days > 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Las Vegas' AND c.country_name = 'USA' AND fs.stop_days = 1 AND f.arrival_time = '2022-05-20 18:00:00';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time = '23:00:00' AND f.to_airport = 'ATL' AND f.to_airport = 'STL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Philadelphia' AND c.city_name = 'San Francisco' AND f.airline_code = 'AA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_day = 'Sunday' AND f.from_airport = 'MILW' AND f.airline_flight = 'AIR'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PIT'   AND fs.arrival_airport = 'NYC';
SELECT aircraft_code FROM flight WHERE departure_time = '08:00:00' AND to_airport = 'SFO' AND flight_id = 'FL001';
The provided SQL query does not contain any information related to ground transport in Seattle, so I am unable to extract the requested data from the provided context.
SELECT flight_id, fare_id, from_airport, to_airport, round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE from_airport = 'PIT' AND to_airport = 'BOS' ORDER BY round_trip_cost ASC;
SELECT flight_id, flight_number, arrival_time FROM flight WHERE departure_time >= '17:00' AND arrival_time <= '20:00' AND from_airport = 'BOS' AND to_airport = 'ATL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.arrival_time BETWEEN '14:00:00' AND '17:00:00' AND f.from_airport = 'ATL' AND f.to_airport = 'SFO';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Baltimore' AND c.city_name = 'Philadelphia';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'SFO' AND fs.arrival_airport = 'DAL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston' AND c.city_name = 'San Francisco' AND fs.stop_days > 3;
SELECT flight.* FROM flight JOIN fare ON flight.flight_id = fare.flight_id JOIN flight_stop ON flight.flight_id = flight_stop.flight_id WHERE fare.round_trip_required = 1 AND fare.from_airport = 'DAL' AND fare.to_airport = 'BAL' ORDER BY fare.fare_id;
The provided context does not contain any information regarding flights departing from Oakland to Boston, so I am unable to extract the requested data from the provided context.
SELECT flight.flight_id FROM flight WHERE flight.departure_time = (     SELECT MIN(flight.departure_time)     FROM flight     WHERE flight.to_airport = 'ATL'     AND flight.departure_date = '2023-10-27' );
SELECT flight_id FROM flight WHERE departure_airport = 'DAL' AND arrival_airport = 'BOS' ORDER BY departure_time ASC LIMIT 1;
UPDATE flight SET departure_airport = 'DENVER' WHERE to_airport = 'PITTSBURGH';
SELECT flight.flight_id, flight.departure_time FROM flight WHERE flight.to_airport = 'STL' AND flight.departure_time = DATE_ADD(NOW(), INTERVAL 1 DAY) ORDER BY flight.departure_time ASC LIMIT 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'MEMPH' AND fs.arrival_airport = 'CHARLOTTE';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Philadelphia' AND c.city_name = 'Dallas' AND fs.stop_days = 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'OAKL' AND fs.arrival_airport = 'BOS'
The provided SQL query does not contain any information regarding costs of Denver rental cars, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.fare_id FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.from_airport = 'MSP'   AND f.to_airport = 'SDQ'   AND f.booking_class = 'ECONOMY'
SELECT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.arrival_time, f.departure_time, f.flight_days, f.connections, f.meal_code, f.departure_time FROM flight f WHERE f.from_airport = 'ATL' AND f.to_airport = 'DEN'
SELECT DISTINCT airline_code FROM flight WHERE departure_airport = 'ATL' ORDER BY airline_code;
SELECT * FROM flight WHERE departure_airport = 'OAKL' AND arrival_airport = 'DALS' AND flight_date = '2023-12-16';
SELECT f.airline_code FROM flight f JOIN airline a ON f.airline_code = a.airline_code WHERE f.to_airport = 'BOS' AND f.from_airport = 'ATL';
SELECT f.fare_id, f.fare_basis_code FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_time < '12:00' AND f.from_airport = 'BOS' AND f.to_airport = 'PIT'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Denver' AND c.city_name = 'Philadelphia';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Dallas' AND c.city_name = 'Pittsburgh' AND f.flight_date = '2023-07-08';
SELECT f.flight_id, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_day = 20 AND f.from_airport = 'PHL' AND f.airline_code = 'UA' AND f.arrival_time >= '09:00:00';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PHL' AND fs.arrival_airport = 'BAL'
SELECT * FROM flight WHERE to_airport = 'OAKNL' AND from_airport = 'BOS' AND EXISTS (     SELECT 1     FROM flight_stop     WHERE departure_airline = 'DALW'     AND arrival_flight_number = 12345 );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days >= 1 AND f.departure_time BETWEEN '08:00:00' AND '12:00:00' AND f.from_airport = 'SFO' AND f.to_airport = 'PIT';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Columbus' AND c.city_name = 'Baltimore';
The provided context does not contain any information regarding the SQL query to translate the question, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time BETWEEN '14:00:00' AND '17:00:00' AND f.to_airport = 'PHL' AND f.from_airport = 'DAL';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.from_airport = 'DAL'   AND flight.to_airport = 'BAL'   AND fare.restriction_code = 'DELTA';
The provided context does not contain any information regarding the aircraft type used on a flight when it leaves at 555, so I am unable to extract the requested data from the provided context.
SELECT flight_id FROM flight WHERE departure_airport = 'BOS'   AND arrival_airport = 'OAK'   AND departure_time = '08:38:00'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Chicago' AND f.arrival_time = 'Saturday 07:00' AND f.to_airport = 'O'
The provided text does not contain any information regarding the code "y", so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id JOIN fare_basis fb ON ff.fare_basis_code = fb.code WHERE f.from_airport = 'BOS' AND f.to_airport = 'PHL';
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight FROM flight f WHERE f.from_airport = 'WA' AND f.to_airport = 'DEN';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PIT' AND fs.arrival_airport = 'ATL';
The provided context does not contain any information regarding ground transportation at San Francisco, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.arrival_time = 'Wednesday 6:00 PM' AND f.from_airport = 'Phoenix' AND f.to_airport = 'Milwaukee';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Atlanta'
The provided text does not contain any information regarding the "yn code", so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN date_day d ON fs.stop_day = d.day_number WHERE f.to_airport = 'ATL'   AND f.departure_date = '2023-10-23'   AND f.flight_day = 'Wednesday' ORDER BY f.arrival_time DESC;
SELECT flight_id FROM flight WHERE arrival_time >= '16:00:00' AND departure_airport = 'BOS' AND flight_id NOT IN (     SELECT flight_id     FROM flight     WHERE arrival_time < '16:00:00'     AND departure_airport = 'WAI' );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'SFO'   AND fs.arrival_airport = 'DCA';
SELECT f.flight_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston'   AND f.arrival_time = (     SELECT MAX(arrival_time)     FROM flight     WHERE to_airport = 'Atlanta'       AND departure_time <= '2023-11-07'   );
SELECT f.flight_id, f.departure_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Oakland'   AND f.departure_time BETWEEN '08:00:00' AND '12:00:00'
SELECT * FROM flight WHERE departure_airport = 'PHL' AND arrival_time = '16:00:00' AND to_airport = 'DEN';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Kansas City' AND f.arrival_date = '2022-05-20' AND fs.stop_days = 1 AND f.to_airport = 'Burbank'
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f WHERE f.to_airport = 'DET'   AND f.departure_date = '2023-10-22'   AND f.stops = 1;
SELECT flight.flight_id, MIN(fare.round_trip_cost) AS cheapest_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id JOIN flight_leg ON fare.flight_id = flight_leg.flight_id WHERE flight.from_airport = 'ATL' AND flight.to_airport = 'PIT' GROUP BY flight.flight_id;
SELECT f.* FROM flight f WHERE f.from_airport = 'PHL' AND f.to_airport = 'DAL';
SELECT COUNT(*) FROM flight WHERE departure_time = CURDATE()   AND airline_flight = 'United'   AND flight_days = 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Baltimore' AND c.city_name = 'San Francisco';
SELECT DISTINCT a.aircraft_code FROM flight f JOIN aircraft a ON f.aircraft_code = a.aircraft_code WHERE f.airline_code = 'CAN';
SELECT * FROM flight WHERE departure_airport = 'BALMD' AND arrival_time > 2100;
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.departure_time = '2023-10-27 00:00:00' AND f.from_airport = 'PIT' AND f.to_airport = 'ATL';
SELECT f.* FROM flight f WHERE f.from_airport = 'DENVER' AND (f.to_airport = 'PITTSBURGH' OR f.to_airport = 'ATLANTA') ORDER BY f.flight_days;
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Baltimore' AND f.arrival_time = '2023-10-27 19:00:00';
SELECT f.flight_id, f.arrival_time, f.flight_number, c.city_name FROM flight f JOIN city c ON f.from_airport = c.city_name WHERE f.to_airport = 'OAKLAND' AND f.from_airport = 'PHILADELPHIA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Chicago' AND f.arrival_day = 'Saturday'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.to_airport = fs.stop_airport WHERE fs.stop_airport <> 'Love Field'
SELECT f FROM flight f WHERE departure_time = (     SELECT MIN(departure_time)     FROM flight     WHERE from_airport = 'BOS' );
SELECT * FROM flight WHERE departure_time >= '2023-04-06 06:00:00' AND from_airport = 'TAMPA FL' AND to_airport = 'CHARLOTTE NC';
SELECT flight_id, fare_id FROM flight WHERE from_airport = 'MEMPH' AND to_airport = 'MIAM' ORDER BY fare_id LIMIT 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.stop_days = 2 AND f.arrival_time BETWEEN '17:00:00' AND '19:00:00' AND f.airline_code = 'DAL'
SELECT EXISTS(     SELECT 1     FROM airport     WHERE airport_code = 'DAL'     AND distance_to('DAL', 'DTX') <= 10 );
SELECT f.*
SELECT * FROM flight WHERE departure_airport = 'PHL' AND arrival_date = '2023-04-16' AND arrival_time = '20:00';
SELECT f.flight_id, f.from_airport, f.to_airport, f.flight_days, f.arrival_time, f.fare_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Houston' AND c.city_name = 'Las Vegas';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Jose' AND c.city_name = 'St. Paul';
The provided context does not contain any information regarding the number of seats in a 734, so I am unable to extract the requested data from the provided context.
The provided text does not contain any information regarding the term "ewr", so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.arrival_time, f.flight_number FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.flight_id = 813 AND fs.stop_days = 1 AND EXISTS (   SELECT 1   FROM flight_stop   WHERE flight_id = fs.flight_id   AND arrival_time > fs.arrival_time );
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.distance FROM flight f WHERE f.from_airport = 'PITTSBURGH' AND f.to_airport = 'NEW_YORK_CITY';
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.arrival_time = DATE_ADD(NOW(), INTERVAL 1 DAY)
The provided context does not contain any information regarding the abbreviation of any airline, so I am unable to extract the requested data from the provided context.
The provided context does not contain any information regarding the definition of airline, so I am unable to extract the requested data from the provided context.
The provided context does not contain any information regarding ground transportation in Denver, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_flight, f.meal_code FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.from_airport = 'PHOENIX' AND f.to_airport = 'DENVER';
SELECT * FROM flight WHERE departure_time = '15:00:00' AND from_airport = 'WA' AND destination_airport = 'DEN';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Orlando' AND c.city_name = 'San Diego' AND f.aircraft_code_sequence = '737';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.departure_time = '718' AND flight.to_airport = 'LASV' AND flight.to_airport = 'NYC';
The provided context does not contain any information regarding ground transportation in Denver, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Pittsburgh' AND c.city_name = 'Denver'
The provided context does not contain any information regarding ground transport in San Francisco, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time < '12:00:00' AND f.airline_code = 'NW'
SELECT f.* FROM flight f WHERE f.to_airport = 'GENERAL MITCHELL INTERNATIONAL';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'DENV' AND fs.arrival_airport = 'PHL';
The provided context does not contain any information regarding limousine services in Boston, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f WHERE f.from_airport = 'BAL'
The provided context does not contain any information regarding the restriction ap/80, so I am unable to extract the requested data from the provided context.
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.from_airport = 'DENV'   AND flight.to_airport = 'PIT'
SELECT f.airline_code FROM flight f JOIN airline a ON f.airline_code = a.airline_code WHERE f.to_airport = 'BOS' AND f.from_airport = 'SFO';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Pittsburgh' AND c.city_name = 'San Francisco';
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.from_airport = 'BOS' AND f.to_airport = 'PHL';
SELECT f.flight_id, f.flight_number, f.arrival_time, f.from_airport, f.airline_name
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'CHI' AND f.arrival_time >= '2023-06-17 19:00:00'
SELECT f.flight_id, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Atlanta' ORDER BY f.arrival_time;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.departure_time BETWEEN '2023-10-27 17:00:00' AND '2023-10-27 21:00:00' AND f.to_airport = 'TOR' AND fs.stop_time BETWEEN 530 AND 700;
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight FROM flight f WHERE f.from_airport = 'ATL'   AND f.to_airport = 'PIT';
SELECT f.flight_id, f.departure_time, f.arrival_time FROM flight f WHERE f.to_airport = 'DCA'   AND f.departure_time = 'Tuesday 08:00:00'   AND f.arrival_time = 'Philadelphia 10:00:00';
SELECT DISTINCT a.airport_name FROM airport a JOIN flight f ON a.airport_code = f.from_airport;
SELECT f.flight_id, f.departure_time, f.arrival_time FROM flight f WHERE f.to_airport = 'DENV'   AND f.departure_date = '2023-10-21'   AND f.flight_number = 12345;
SELECT f.flight_id, f.departure_time FROM flight f WHERE EXISTS (     SELECT 1     FROM flight_stop fs     WHERE fs.arrival_flight_number = f.flight_id );
The provided SQL query does not contain any information related to ground transportation from Boston Airport to Boston Downtown, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id
SELECT f.flight_id, f.flight_number, f.from_airport, f.airline_flight, f.departure_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_airport = 'DENV' AND f.to_airport = 'SANdiego';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco' AND c.country_name = 'United States' AND MONTH(fs.arrival_time) = 12
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 0 AND f.arrival_time < '12:00:00' AND f.to_airport = 'BALtimore' AND f.airline_code = 'DAL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.stop_days = 2 AND f.arrival_time >= DATE_ADD(NOW(), INTERVAL 2 DAY) AND f.arrival_time < DATE_ADD(NOW(), INTERVAL 4 DAY);
SELECT f.fare_id, c.class_description FROM flight f JOIN fare f ON f.flight_id = f.flight_id JOIN class_of_service c ON c.booking_class = f.booking_class WHERE f.from_airport = 'PIT' AND f.to_airport = 'ATL'
SELECT EXISTS(     SELECT 1     FROM airport_service     WHERE airport_code = 'ATL'     AND airport_name = 'Atlanta Airport' );
SELECT f.* FROM flight f WHERE f.departure_airport = 'BOS' AND f.arrival_airport = 'SFO' ORDER BY f.flight_id DESC;
SELECT * FROM flight WHERE to_airport = 'CHARLOTTE' AND departure_date = '2023-10-27' AND arrival_airport = 'ATLANTA';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.from_airport = 'OAKL'   AND flight.to_airport = 'ATL'   AND fare.restriction_code = 'FIRST_CLASS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'NSH'   AND fs.arrival_airport = 'SEA';
SELECT fare.fare_id, fare.round_trip_cost FROM flight_fare AS fare JOIN fare_basis AS fb ON fare.fare_basis_code = fb.code WHERE fare.from_airport = 'ATL'   AND fare.to_airport = 'DEN'   AND fb.class_type = 'FIRST_CLASS';
SELECT f.flight_id, f.arrival_time, f.flight_number, c.city_name FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'Newark' AND c.city_name = 'Cleveland' AND f.day_name = 'Tuesday';
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.from_airport = 'IND'   AND flight.to_airport = 'SEA'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON fs.stop_number = fl.stop_number JOIN days d ON fl.leg_flight = d.days_code JOIN airport a ON fl.from_airport = a.airport_code WHERE d.day_name = 'Monday' AND f.restriction_code = 'FIRSTCLASS'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.arrival_time = 'Saturday 08:00:00' AND f.to_airport = 'SEA'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.stop_days = 1 AND f.departure_time = '2023-10-27 19:00:00' AND f.to_airport = 'LAX'
SELECT f.* FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.to_airport = 'IND' AND f.departure_date = '2023-12-27' AND ff.fare_basis_code = 'economy';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'SFO' AND f.from_airport = 'PHI' AND MONTH(f.departure_time) = 9 AND f.year = 2023;
SELECT flight_id FROM flight WHERE from_airport = 'BOS' AND to_airport = 'OAK' ORDER BY departure_time ASC LIMIT 1;
The provided context does not contain any information regarding ground transportation in Washington DC, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'WAI'   AND fs.arrival_airport = 'SFO';
The provided context does not contain any information regarding the SQL query for explaining restriction, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_day = 5 AND f.arrival_time BETWEEN '17:00:00' AND '19:00:00' AND f.from_airport = 'PHL' AND f.to_airport = 'OAK';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN food_service fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.arrival_time = '2023-10-27 19:00:00' AND f.meal_code = 'MEALCODE'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Long Beach' AND c.city_name = 'St. Louis' AND EXISTS (   SELECT 1   FROM flight_stop   WHERE flight_id = f.flight_id   AND stop_days = 2 );
SELECT f.flight_days FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Kansas City'   AND f.to_airport = 'St. Paul';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Los Angeles' AND c.city_name = 'Pittsburgh';
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.airline_flight, f.meal_code FROM flight f WHERE f.from_airport = 'DENV' AND f.to_airport = 'PHI';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PHL' AND fs.arrival_airport = 'SFO';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'DENV' AND f.arrival_date = '2023-10-15' AND c.city_name = 'SAN FRANCISCO';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Denver' AND c.city_name = 'Salt Lake City';
The provided SQL code does not contain any information regarding classes of service, so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time BETWEEN '17:00:00' AND '19:00:00' AND f.to_airport = 'BWI' AND f.airline_code = 'UA' ORDER BY f.flight_id;
SELECT f.flight_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days >= 1 AND f.from_airport = 'DAL' AND f.to_airport = 'HOU' ORDER BY f.departure_time;
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.stops, f.flight_days, f.connections FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_number = 1 AND f.from_airport = 'BALtimore' AND f.to_airport = 'Seattle'
SELECT * FROM flight WHERE to_airport = 'SFO' AND from_airport = 'BOS' AND EXISTS (     SELECT 1     FROM flight_stop     WHERE departure_airline = 'DAL'     AND arrival_flight_number = 12345 );
SELECT airport_location FROM airport WHERE airport_code = 'SFO';
The provided context does not contain any information regarding the airline "dl", so I am unable to extract the requested data from the provided context.
SELECT f.* FROM flight f WHERE f.arrival_time = (     SELECT MAX(arrival_time)     FROM flight     WHERE to_airport = 'LOVEFL' );
SELECT f.* FROM flight f WHERE f.arrival_airport = 'GENERAL MITCHELL INTERNATIONAL AIRPORT';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'NYC' AND f.from_airport = 'LAX' AND EXISTS (     SELECT 1     FROM flight_stop     WHERE flight_id = f.flight_id     AND stop_days = 1     AND stop_airport IN ('MIL') );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Philadelphia' AND c.city_name = 'Dallas' AND f.airline_code = 'AA';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_airport = 'WC' AND fs.stop_destination = 'CIN'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco'   AND f.arrival_time = '2023-10-27'   AND f.from_airport = 'SFO'
SELECT flight.fare_id FROM flight JOIN fare_basis ON flight.flight_id = fare_basis.flight_id WHERE flight.from_airport = 'BOS'   AND fare_basis.season = 'OFF-SEASON'   AND flight.stops = 1   AND fare_basis.booking_class = 'economy';
SELECT f.* FROM flight f WHERE f.arrival_time = (SELECT MAX(arrival_time) FROM flight WHERE departure_airport = 'SFO' AND departure_time <= f.departure_time);
The provided context does not contain any information regarding ground transport available in Minneapolis, so I am unable to extract the requested data from the provided context.
The provided context does not contain any information regarding the type of airplane, so I am unable to extract the requested data from the provided context.
SELECT * FROM flight WHERE departure_time < '9:00:00' AND from_airport = 'PITTSBURGH' AND to_airport = 'PHILADELPHIA';
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.from_airport = 'DAL' AND f.to_airport = 'BAL' AND fb.class_description = 'Economy';
SELECT airport_name FROM airport WHERE airport_code = 'TAMPA';
SELECT f.* FROM flight f WHERE f.departure_time = CURDATE();
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.from_airport = 'ATL' AND f.to_airport = 'BAL'
SELECT f.flight_id, f.fare_id, f.round_trip_cost FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.from_airport = 'BALtimore' AND f.to_airport = 'Dallas' AND f.month_number = 7 AND f.day_name = '29';
SELECT f.* FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.to_airport = 'HOUSTON' AND f.from_airport = 'LAS VEGAS';
SELECT * FROM flight WHERE departure_airport = 'JFK' AND arrival_airport = 'MIA' AND day_name = 'Tuesday';
SELECT f.flight_id, f.arrival_time, f.flight_number, c.city_name FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'SFO' AND f.from_airport = 'DEN'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'DAL' AND fs.arrival_airport = 'TAM'
SELECT * FROM flight WHERE departure_airport = 'SFO' AND airline_code = 'UA';
SELECT f.flight_id, f.fare_id FROM flight f JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE f.to_airport = 'BALtimore'   AND f.from_airport = 'Philadelphia';
SELECT * FROM flight WHERE departure_date = '2023-10-22'   AND from_airport = 'PHOENIX'   AND to_airport = 'DETROIT';
SELECT f.*
SELECT flight_id FROM flight WHERE from_airport = 'ATL' AND to_airport = 'DEN' AND meal_code IS NOT NULL ORDER BY departure_time ASC LIMIT 1;
SELECT f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'SFO'   AND fs.arrival_airport = 'ATL'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'DCA' AND f.arrival_time >= '2023-12-02' AND f.arrival_time < '2023-12-10';
SELECT f FROM flight f WHERE f.from_airport = 'BALMD' AND f.to_airport = 'SFO' AND f.arrival_time = '20:00:00' AND f.day = 'Fri'
SELECT f.flight_id, f.departure_time, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'BOS' AND fs.arrival_airport = 'SFO';
SELECT DISTINCT aircraft_code FROM flight WHERE departure_time < '18:00' AND to_airport = 'ATL' AND airline_code = 'DAL';
SELECT * FROM flight WHERE departure_time = DATE_ADD(NOW(), INTERVAL 1 DAY) AND from_airport = 'COLUMBUS' AND to_airport = 'NASHVILLE';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'SFO'   AND f.departure_date = '2091-08-31'   AND f.airline_code = 'DAL';
SELECT f.* FROM flight f JOIN fare f ON f.flight_id = f.flight_id JOIN class_of_service c ON f.booking_class = c.booking_class WHERE f.from_airport = 'NYC' AND f.arrival_date = '2023-10-27' AND f.departure_airline = 'AA'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.to_airport = 'PHOENIX' AND f.airline_code = 'AA' AND f.day = 'WED'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Tampa' AND c.city_name = 'Cincinnati';
The provided context does not contain any information regarding ground transportation in Philadelphia, so I am unable to extract the requested data from the provided context.
The provided context does not contain any information regarding rental cars in Washington DC, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.flight_number, f.from_airport, f.to_airport, f.arrival_time, f.departure_time
SELECT f.fare_id, f.fare_basis_code, f.round_trip_cost FROM flight f JOIN fare_basis fb ON f.fare_basis_code = fb.farebasiscode WHERE f.to_airport = 'DAL' AND f.from_airport = 'SFO'
The provided context does not contain any information regarding the distance from downtown to the airport in Dallas, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.fare_id, f.round_trip_cost FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.from_airport = 'SANJOSE'   AND f.to_airport = 'SALT LAKE CITY'   AND f.round_trip_required = 1;
SELECT fare.fare_id FROM flight_fare JOIN fare ON fare.flight_id = flight.flight_id WHERE flight.from_airport = 'SFO'   AND flight.to_airport = 'DFW'   AND flight.flight_number = 852;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_time = '2023-10-27 18:00' AND f.to_airport = 'PITTSBURGH' AND f.to_airport = 'PHILADELPHIA';
SELECT flight_fare.fare_id FROM flight_fare JOIN fare_basis ON flight_fare.fare_basis_code = fare_basis.fareBASISCODE WHERE flight_fare.from_airport = 'DAL'   AND flight_fare.to_airport = 'BAL'   AND fare_basis.season = 'SUMMER'   AND fare_basis.booking_class = 'economy';
SELECT f.flight_id, f.departure_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_time BETWEEN 06:00:00 AND 10:00:00 AND f.from_airport = 'BOS' AND f.to_airport = 'DEN';
SELECT flight.fare_id, MIN(flight.round_trip_cost) FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.from_airport = 'DENV' AND flight.to_airport = 'ATL' GROUP BY flight.fare_id;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.from_airport = 'BALtimore' AND f.arrival_time = 'Tuesday 07:00'
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.stops, f.flight_days, f.connections, f.arrival_airport, f.airline_flight, f.meal_code FROM flight f WHERE f.from_airport = 'CHI' AND f.to_airport = 'NSH';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_time >= '1992-01-01' AND f.departure_time < '1992-02-01' AND c.city_name = 'Boston' AND c.city_name = 'San Francisco';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.departure_time = '2023-10-27 19:00:00' AND f.to_airport = 'SFO' AND f.airline_code = 'SFO'
SELECT COUNT(*) FROM flight WHERE from_airport = 'BOS'   AND arrival_airport = 'ATL'   AND stopovers = 0;
SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.stops, f.flight_days, f.connections FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Oakland' AND c.city_name = 'Boston' AND f.airline_code = 'TWA';
SELECT f.flight_id, f.flight_number, f.arrival_time FROM flight f WHERE f.to_airport = 'LASV'   AND f.restriction_code = 'NONSTOP'   AND NOT EXISTS (     SELECT 1     FROM flight_stop s     WHERE s.arrival_flight_number = f.flight_id   );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.from_airport = 'BOS' AND f.arrival_time < '05:00:00' AND f.day_name = 'Thursday'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Atlanta'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_day = 1 AND f.departure_time = '2023-10-27 00:00:00'
SELECT DISTINCT airline_code FROM flight WHERE to_airport = 'PITTSBURGH'
SELECT fare.round_trip_cost FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE flight.to_airport = 'DUB'   AND flight.from_airport = 'DEN'   AND flight.restriction_code = 'UA270';
SELECT DISTINCT airline_code FROM flight WHERE to_airport = 'PIT'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN airport a ON fs.arrival_airport = a.airport_code WHERE a.city_name = 'Los Angeles'
SELECT f.flight_id, f.fare_id, f.flight_number, f.arrival_time, f.departure_time, f.from_airport, f.to_airport, f.aircraft_code_sequence FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_fare ff ON f.flight_id = ff.flight_id WHERE fs.stop_number BETWEEN 1 AND 5 AND f.from_airport = 'PIT' AND f.to_airport = 'PHI';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Toronto' AND f.to_airport = 'SFO';
SELECT fare.fare_id FROM flight_fare JOIN fare_basis ON fare.fare_basis_code = fare_basis.code WHERE flight_id = (     SELECT flight_id     FROM flight     WHERE to_airport = 'DAL'       AND departure_time = '2023-10-27 19:00:00' ) AND fare_basis.season = 'FALL' AND fare_basis.basis_days = 7;
SELECT * FROM flight WHERE departure_time >= '18:00:00' AND to_airport = 'BOS' AND flight_day = 'WED' AND flight_id IN (   SELECT flight_id   FROM flight   WHERE departure_time >= '18:00:00'   AND to_airport = 'ATL' );
SELECT * FROM flight WHERE to_airport = 'INDXJ' AND airline_code = 'USAA' AND departure_time BETWEEN '17:00:00' AND '19:00:00';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.arrival_date = CURDATE() AND f.to_airport = 'BOS' AND f.to_airport = 'DEN'
SELECT f.to_airport, f.flight_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'PIT' AND f.to_airport = 'DTN'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Milwaukee' AND c.city_name = 'Montreal';
SELECT flight.flight_id FROM flight WHERE departure_airport = 'BOS' AND destination_airport = 'PHL' ORDER BY flight.departure_time LIMIT 1;
SELECT f.flight_id FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_number = 1 AND f.departure_time >= '2023-06-26' AND f.departure_time < '2023-06-27';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Philadelphia' AND f.to_airport = 'Dallas' AND fs.stop_days = 2;
SELECT DISTINCT f.airline_code FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Pittsburgh' AND f.arrival_date = '2023-09-02' AND f.arrival_time = '12:00:00';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston' AND c.city_name = 'San Francisco';
SELECT f.* FROM flight f WHERE f.to_airport = 'BOS'   AND f.departure_date = '2023-07-29'   AND f.flight_number = 12345;
SELECT DISTINCT f.aircraft_code FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN airport a ON fs.to_airport = a.airport_code WHERE a.city_name = 'Pittsburgh'   AND fs.arrival_flight_number = 12345;
SELECT flight_id, departure_time FROM flight WHERE to_airport = 'BOS'   AND departure_time = 'MONDAY 08:00:00'
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE f.to_airport = 'CINcinnati' AND fs.stop_number = 417;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'DAL' AND fs.arrival_airport = 'ATL';
SELECT EXISTS(     SELECT 1     FROM airport_service     WHERE airport_code = 'BOS'     AND direction = 'GROUND' );
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.departure_airport = 'SFO' AND fs.arrival_airport = 'LAS';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE f.departure_date = '2023-10-27'   AND f.from_airport = 'HOUSTON'   AND f.to_airport = 'MILWAUKEE'   AND f.day = 'friday'   AND f.airline_code = 'AA';
The provided context does not contain any information regarding limousine fares, so I am unable to extract the requested data from the provided context.
SELECT f.flight_id, f.departure_time, f.arrival_time, f.flight_number, f.from_airport, f.to_airport, f.airline_code FROM flight f WHERE f.departure_airport = 'DENV' AND f.arrival_airport = 'PIT';
SELECT f.flight_id, f.arrival_time FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id WHERE fs.stop_days = 1 AND f.to_airport = 'SFO' AND f.airline_code = 'SWA';
SELECT f.* FROM flight f JOIN fare f ON f.flight_id = f.flight_id WHERE f.to_airport = 'SEA'   AND f.from_airport = 'MSP'   AND f.round_trip_required = 1;
SELECT EXISTS(     SELECT 1     FROM airport_service     WHERE airport_code = 'PHOENIX'     AND direction = 'TO' );
SELECT f.* FROM flight f WHERE f.from_airport = 'SJC'   AND f.arrival_time = '2023-06-03 00:00:00'   AND f.flight_day = 'Friday'   AND f.arrival_time = '00:00:00';
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'San Francisco' AND fs.stop_days = 1 AND f.arrival_time >= '2023-10-27 10:00:00' AND f.arrival_time <= '2023-10-27 22:00:00';
SELECT flight_id, fare_id FROM flight JOIN fare ON flight.flight_id = fare.flight_id WHERE from_airport = 'DENVER' AND to_airport = 'PITTSBURGH' ORDER BY fare_id LIMIT 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN flight_leg fl ON f.flight_id = fl.flight_id WHERE fs.stop_airport = 'SAN_DIEGO' AND f.aircraft_code_sequence = '767'
SELECT f.airline_code FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Boston'   AND c.city_name = 'Washington DC'   AND fs.stop_days > 1;
SELECT f.* FROM flight f JOIN flight_stop fs ON f.flight_id = fs.flight_id JOIN city c ON fs.stop_airport = c.city_code WHERE c.city_name = 'Dallas' AND f.arrival_time < '12:00:00'
