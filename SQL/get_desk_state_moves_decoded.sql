-- FUNCTION: public.get_desk_state_moves_decoded(integer, integer)

-- DROP FUNCTION IF EXISTS public.get_desk_state_moves_decoded(integer, integer);

CREATE OR REPLACE FUNCTION public.get_desk_state_moves_decoded(
	_desk_id integer,
	_state integer)
    RETURNS TABLE(state_insert_id integer, moves jsonb)
    LANGUAGE 'sql'
    COST 100
    STABLE PARALLEL SAFE
    ROWS 1000

AS $BODY$
SELECT "State_Moves".state_id, msgpack_decode("State_Moves".moves)
FROM "State_Moves"
WHERE state_id = (SELECT "States".id
				  FROM "States"
				  WHERE desk_id=_desk_id
				  AND state=_state)
$BODY$;

ALTER FUNCTION public.get_desk_state_moves_decoded(integer, integer)
    OWNER TO postgres;
