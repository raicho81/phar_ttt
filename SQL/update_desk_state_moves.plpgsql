-- PROCEDURE: public.update_state_moves(bytea, integer)

-- DROP PROCEDURE IF EXISTS public.update_state_moves(bytea, integer);

CREATE OR REPLACE PROCEDURE public.update_state_moves(
	IN _moves bytea,
	IN _state_id integer)
LANGUAGE 'sql'
AS $BODY$
UPDATE "State_Moves"
    SET moves = _moves
        WHERE "State_Moves".state_id = _state_id
$BODY$;

