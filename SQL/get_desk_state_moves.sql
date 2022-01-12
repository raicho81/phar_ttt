-- FUNCTION: public.get_desk_state_moves(integer, integer)

-- DROP FUNCTION IF EXISTS public.get_desk_state_moves(integer, integer);

CREATE OR REPLACE FUNCTION public.get_desk_state_moves(
	_desk_id integer,
	_state integer)
    RETURNS TABLE(state_insert_id integer, moves bytea) 
    LANGUAGE 'sql'
    COST 100
    STABLE PARALLEL SAFE 
    ROWS 1

AS $BODY$
SELECT "State_Moves".state_id, "State_Moves".moves
FROM "State_Moves"
WHERE state_id = (SELECT "States".id
				  FROM "States"
				  WHERE desk_id=_desk_id
				  AND state=_state)
$BODY$;

ALTER FUNCTION public.get_desk_state_moves(integer, integer)
    OWNER TO postgres;
