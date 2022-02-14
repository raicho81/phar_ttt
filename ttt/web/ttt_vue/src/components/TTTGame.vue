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
            game_data: {
                ttt_play_msg: null,
                ttt_player: null,
                game_uuid: null,
                desk_size: null,
                desk: null,
                game_state: null
            }
        }
    },
    methods: {
        async loadDeskSizes() {
            const res = await fetch(
                `http://127.0.0.1:8000/tttweb/load_desks/`
            )
            this.desks = await res.json()
            this.selected = this.desks.desk_sizes.length > 0 ?
                this.desks.desk_sizes[0] : -1
        },
        async startNewGame() {
            const res = await fetch(
                `http://127.0.0.1:8000/tttweb/start_game/?player_name=${this.player_name}&desk_size=${this.selected}`
            )
            this.game_data = await res.json()
        },
        async makeMove() {

        }
    },
    mounted() {
        this.loadDeskSizes()
    }    
}
</script>

<template>
    <span v-if="!game_data.game_started">
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
        <TTTDesk :desk="game_data.desk"/>
    </span>
</template>
