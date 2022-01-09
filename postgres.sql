-- Adminer 4.8.1 PostgreSQL 14.1 (Debian 14.1-1.pgdg110+1) dump

CREATE SEQUENCE "Desks_id_seq" INCREMENT  MINVALUE  MAXVALUE  CACHE ;

CREATE TABLE "public"."Desks" (
    "id" integer DEFAULT nextval('"Desks_id_seq"') NOT NULL,
    "size" integer NOT NULL,
    "total_games_played" integer DEFAULT '0' NOT NULL,
    CONSTRAINT "Desks_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


CREATE SEQUENCE "State_Moves_id_seq" INCREMENT  MINVALUE  MAXVALUE  CACHE ;

CREATE TABLE "public"."State_Moves" (
    "id" integer DEFAULT nextval('"State_Moves_id_seq"') NOT NULL,
    "state_id" integer NOT NULL,
    "moves" bytea NOT NULL,
    CONSTRAINT "State_Moves_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "State_Moves_state_id" UNIQUE ("state_id")
) WITH (oids = false);


CREATE SEQUENCE "States_id_seq" INCREMENT  MINVALUE  MAXVALUE  CACHE ;

CREATE TABLE "public"."States" (
    "id" integer DEFAULT nextval('"States_id_seq"') NOT NULL,
    "desk_id" integer NOT NULL,
    "state" integer NOT NULL,
    CONSTRAINT "States_desk_id_state" UNIQUE ("desk_id", "state"),
    CONSTRAINT "States_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "States_desk_id" ON "public"."States" USING btree ("desk_id");

CREATE INDEX "States_state" ON "public"."States" USING btree ("state");


ALTER TABLE ONLY "public"."State_Moves" ADD CONSTRAINT "State_Moves_state_id_fkey" FOREIGN KEY (state_id) REFERENCES "States"(id) ON UPDATE CASCADE ON DELETE CASCADE NOT DEFERRABLE;

ALTER TABLE ONLY "public"."States" ADD CONSTRAINT "States_desk_id_fkey" FOREIGN KEY (desk_id) REFERENCES "Desks"(id) ON UPDATE CASCADE ON DELETE CASCADE NOT DEFERRABLE;

-- 2022-01-09 05:59:07.094681+00