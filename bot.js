const Bot = {
    attack: async (id) => {
        console.info("attacking", id)
        return $.post(
            "/alley/",
            {action: "attack", "player": id, "werewolf": 0, "useitems": 0},
            null,
            "json"
        )
    },

    is_ready: () => {
        let end_time = parseInt($('#timeout').attr('endtime'), 10) * 1000
        console.debug("timer is ", end_time)
        if (isNaN(end_time) || end_time < (+new Date())) {
            console.log("ok to attack")
            return true
        }

        return false
    },

    fight: async (id) => {
        let attack_response = await Bot.attack(id)
        if ("return_url" in attack_response) {
            await AngryAjax.goToUrl(attack_response.return_url)
        }

        if ($("#controls-forward").length) {
            $("#controls-forward").click()
        }

        if (parseInt($('#currenthp').attr('title'), 10) < parseInt($('#maxhp').attr('title'), 10)) {
            let heal_response = await $.post("/player/restorehp/", {"action": "restorehp"}, null, "json")
            updateWallet(heal_response['wallet']);
            setHP(heal_response['hp']);
        } else {
            await Bot.wait(1000)
        }

        const result = "return_url" in attack_response && attack_response.return_url.indexOf("fight") !== -1
        return new Promise((resolve, reject) => {
            resolve(result)
        });
    },

    searchByLevel: async (level_min, level_max) => {
        let r = await $.post(
            "/alley/search/level/",
            "werewolf=0&nowerewolf=1&minlevel=" + level_min + "&maxlevel=" + level_max + "&__ajax=1&return_url=%2Falley%2F"
        )
        $('.column-right').html(r.content);

        let other_id = parseInt($(".fighter2 .user a:last-of-type").attr("href").substring(8), 10)

        let my_stats = $(".fighter1-cell .stats .num").toArray().reduce((i, e, n) => { return i + parseInt($(e).text(), 10) }, 0)
        let other_stats = $(".fighter2-cell .stats .num").toArray().reduce((i, e, n) => { return i + parseInt($(e).text(), 10) }, 0)

        if (my_stats < other_stats) return false

        return other_id
    },

    wait: (ms) => {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

async function fight_em() {
    while (true) {
        while (!Bot.is_ready()) {
            await Bot.wait(1000)
        }

        let id = await Bot.searchByLevel(15, 15)
        if (id === false) continue

        await Bot.fight(id)
    }
}
await fight_em()

// async function fight_em(ids) {
//     for (const id of ids) {
//         while (!Bot.is_ready()) {
//             await Bot.wait(1000)
//         }
//         const res = await Bot.fight(id);
//         console.log(id, res);
//     }
// }
//
// await fight_em(a)
// bot = new Bot()
// while (true) {
//     await fight_em(a)
//     await Bot.wait(600000)
// }