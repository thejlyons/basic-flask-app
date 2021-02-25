const td_start = 'bg-white rounded-start border border-end-0 py-2 px-3';
const td_middle = 'bg-white border-top border-bottom p-2 pl-4';
const td_end = 'bg-white border border-start-0 rounded-end py-2 pl-4';

Vue.component('user', {
    props: ['user', 'index'],
    template: `
        <tr class="user-row gilroy">
            <td class="user-phone text-primary ` + td_start + `">{{ user.phone }}{{ index }}</td>
            <td class="user-location text-primary ` + td_middle + `">{{ user.city }}{{ user.state ? ', ' + user.state : ''}}</td>
            <td class="user-controls ` + td_end + `">
                <button class="btn me-2" v-bind:class="{'btn-warning': user.active, 'btn-outline-warning': !user.active}" @click="$emit('toggle_active', user, index)">{{ user.active ? 'Deactivate' : 'Activate' }}</button> 
                <i class="btn btn-success fas fa-pencil-alt text-white me-2" @click="$emit('set_active', user, index)"></i> 
            </td>
        </tr>
    `
});

Vue.component('user-settings', {
    props: ['user', 'index', 'notes'],
    data: function() {
        return {
            'new_note': ''
        }
    },
    mounted: function() {
        $('[data-bs-toggle="tooltip"]').tooltip();
    },
    methods: {
        submit_note: function() {
            this.$emit('new_note', this.new_note);
            this.new_note = '';
        },
    },
    template: `
        <div class="user-settings gilroy">
            <div class="mb-3">
                <h5 class="text-primary" data-bs-toggle="tooltip" title="Phone neumber">{{ user.phone ? user.phone : 'New User'}}</h5>
                <p class="text-muted">{{ user.city }}{{ user.state ? ', ' + user.state : user.state }}</p>
                <div class="d-flex flex-row justify-content-between">
                    <div v-if="user.active" class="font-md">Purchased via:
                        <a v-if="user.stripe_customer && user.stripe_subscription" v-bind:src="'https://dashboard.stripe.com/subscriptions/' + user.stripe_subscription">Stripe</a>
                        <i v-else-if="user.promo_id" class="fas fa-ticket-alt" data-bs-toggle="tooltip" v-bind:title="user.promo"></i>
                        <i v-else class="fab fa-apple-pay"></i> 
                    </div>
                    <button class="btn ms-auto me-2" v-bind:class="{'btn-warning': user.active, 'btn-outline-warning': !user.active}" @click="$emit('toggle_active', user, index)">{{ user.active ? 'Deactivate' : 'Activate' }}</button>
                </div>
            </div>
            <div class="row">
                <div class="col-6 p-2">
                    <div v-if="!notes || notes.length === 0" class="w-100 text-center text-muted">
                        - No notes -
                    </div>
                    <div v-for="(note, i) in notes">
                        <p class="mb-0">{{ note.note }}</p>
                        <div class="d-flex justify-content-between align-content-center mb-2 font-sm">
                            <span class="text-muted">{{ note.created }}</span>
                            <i class="fas fa-trash-alt text-danger cursor-pointer" @click="$emit('delete_note', note, i)"></i>
                        </div>
                    </div>
                </div>            
                <div class="col-6 p-2">
                    <label for="user-new-note" class="form-label">New Note</label>
                    <textarea class="form-control" id="user-new-note" rows="3" v-model="new_note"></textarea>
                    <br>
                    <button type="button" class="w-100 btn btn-primary btn-block rounded-pill text-white" @click="submit_note()">Save</button>                
                </div>            
            </div>
        </div>
    `
});
