<script setup>
    import TTTDesk from './TTTDesk.vue'
</script>

<script>
export default {
    data() {
        return {
            selected: -1,
            desks: {'desk_sizes': []},
            player_name: 'Input Your Name Here',
            next_move_idx: -1,
            game_data: {
                player_code: null,
                player_id: null,
                game_uuid: null,
                desk_size: null,
                desk: null,
                game_state: null,
                next_player: null,
                player_mark: null,
                win_player: null,
            }
        }
    },
    methods: {
        async loadCSRF(){
            const res = await fetch(
                `http://127.0.0.1:8000/tttweb/get_csrf/`
            )
            let r = await res.json()
            this.csrf_token = r['X-CSRFToken']
        },
        async loadDeskSizes() {
            const res = await fetch(
                `http://127.0.0.1:8000/tttweb/load_desks/`
            )
            this.desks = await res.json()
            this.selected = this.desks.desk_sizes.length > 0 ?
                this.desks.desk_sizes[0] : -1
        },
        async startNewGame() {
            const reqBody = {'player_name': this.player_name, 'desk_size': this.selected}
            const requestOptions = {
                method: "POST",
                mode: 'cors',
                cache: 'no-cache',
                headers: {"Content-Type": "application/json", "X-CSRFToken": this.csrf_token},
                body: (JSON.stringify(reqBody))
            }
            const res = await fetch(
                `http://127.0.0.1:8000/tttweb/start_game/`,
                requestOptions
            )
            var resp = await res.json()
            this.game_data = resp.game_data
        },
        async makeMove(next_move_idx) {
            const reqBody = {'game_uuid': this.game_data.game_uuid, 'next_move_idx': next_move_idx, 'desk_size': this.game_data.desk_size}
            console.log(reqBody)
            const requestOptions = {
                method: "POST",
                mode: 'cors',
                cache: 'no-cache',
                headers: {"Content-Type": "application/json", "X-CSRFToken": this.csrf_token},
                body: (JSON.stringify(reqBody))
            }
            const res = await fetch(
                `http://127.0.0.1:8000/tttweb/make_move/`,
                requestOptions
            )
            var resp = await res.json()
            this.game_data = resp.game_data
        }
    },
    beforeMount(){
        this.loadCSRF()
    },
    mounted() {
        this.loadDeskSizes()
    }
}
</script>

<template>
    <span v-if="game_data.game_uuid == null">
        <p>Player Name <input v-model="player_name" type="text"/>
        Desk Size
        <select v-model="selected">
            <option v-for="ds in desks.desk_sizes" v-bind:value="ds">
                {{ ds }}
            </option>
        </select>
        <button @click="startNewGame">Start New Game</button></p>
    </span>
    <span v-else>
        <p>Game started.</p>
        <p>Player Name: {{ this.game_data.player_name }} </p>
        <TTTDesk :desk="game_data.desk" :player_mark="game_data.player_mark" :player_code="game_data.player_code" @makeMove="makeMove"/>
    </span>
</template>
