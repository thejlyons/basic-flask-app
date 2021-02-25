const td_start = 'bg-white rounded-start border border-end-0 py-2 px-3';
const td_middle = 'bg-white border-top border-bottom p-2 pl-4';
const td_end = 'bg-white border border-start-0 rounded-end py-2 pl-4';


Vue.component('merchant', {
    props: ['merchant'],
    template: `
        <tr class="merchant-row gilroy">
            <td class="merchant-name text-primary ` + td_start + ` d-flex flex-row align-content-start">
                <div class="my-2 me-3" style="height: 60px;">
                    <img v-if="merchant.images && merchant.images.length > 0" class="rounded-3" v-bind:src="merchant.images[0]" style="max-width:100%; max-height:100%;">
                </div>
                <div class="my-2">
                    <h5>{{ merchant.name ? merchant.name : 'New Merchant' }}</h5>
                    <span class="text-muted">Categories</span>
                </div>
            </td>
            <td class="merchant-locations ` + td_middle + `">
                Locations: {{ merchant.num_locations }}
            </td>
            <td class="merchant-social ` + td_middle + `">
                <div class="d-flex justify-content-start align-content-center flex-row w-100">
                    <a v-if="merchant.instagram" class="px-2" v-bind:href="merchant.instagram" target="_blank">
                        <i class="fab fa-instagram"></i>
                    </a>
                    <a v-if="merchant.facebook" class="px-2" v-bind:href="merchant.facebook" target="_blank">
                        <i class="fab fa-facebook"></i>
                    </a>
                    <a v-if="merchant.website" class="px-2" v-bind:href="merchant.website" target="_blank">
                        <i class="fas fa-globe"></i>
                    </a>
                    <span v-if="!merchant.instagram && !merchant.facebook && !merchant.website" class="text-muted">--</span>
                </div>
            </td>
            <td class="merchant-status ` + td_middle + `" style="width: 225px;">
                <div class="w-100 row gilroy-bold font-sm">
                    <div class="col-6">
                        <i class="far" v-bind:class="{'fa-check-square': merchant.approved, 'fa-square': !merchant.approved}"></i> Approved
                    </div>                
                    <div class="col-6">
                        <i class="far" v-bind:class="{'fa-check-square': merchant.coming_soon, 'fa-square': !merchant.coming_soon}"></i> Coming Soon
                    </div>
                </div>
            </td>
            <td class="merchant-controls ` + td_end + `">
                <i class="btn btn-success fas fa-pencil-alt text-white me-2" @click="$emit('set_active', merchant)"></i> 
                <i class="btn btn-danger fas fa-trash-alt" @click="$emit('delete_merchant', merchant)"></i> 
            </td>
        </tr>
    `
});

Vue.component('merchant-settings', {
    props: ['name', 'instagram', 'facebook', 'website', 'notes', 'terms_agreed', 'welcome_email', 'go_live_text'],
    data: function() {
        return {
            'local_name': this.name,
            'local_instagram': this.instagram,
            'local_facebook': this.facebook,
            'local_website': this.website,
            'local_terms_agreed': this.terms_agreed,
            'local_welcome_email': this.welcome_email,
            'local_go_live_text': this.go_live_text,
            'new_note': ''
        }
    },
    methods: {
        submit_note: function() {
            console.log('Submitting')
            this.$emit('new_note', this.new_note);
            this.new_note = '';
        }
    },
    template: `
        <div class="merchant-settings gilroy">
            <div class="mb-3">
                <label for="merchant-name" class="form-label">Merchant Name</label>
                <input type="text" class="form-control" id="merchant-name" v-model="local_name" v-on:input="$emit('propogate_data', 'name', local_name)">
            </div>
            <div class="row mb-3 border-bottom pb-4">
                <div class="col-12 col-md-4">
                    <label for="merchant-instagram" class="form-label">Instagram</label>
                    <input type="text" class="form-control" id="merchant-instagram" v-model="local_instagram" v-on:input="$emit('propogate_data', 'instagram', local_instagram)">
                </div>
                <div class="col-12 col-md-4">
                    <label for="merchant-facebook" class="form-label">Facebook</label>
                    <input type="text" class="form-control" id="merchant-facebook" v-model="local_facebook" v-on:input="$emit('propogate_data', 'facebook', local_facebook)">
                </div>
                <div class="col-12 col-md-4">
                    <label for="merchant-website" class="form-label">Website</label>
                    <input type="text" class="form-control" id="merchant-website" v-model="local_website" v-on:input="$emit('propogate_data', 'website', local_website)">
                </div>
            </div>
            <div class="row my-2 py-2 border-bottom border-top">
                <h5>Happy Hour Time Slots</h5>
                <div class="col-12 col-sm-4 mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" @change="$emit('propogate_data', 'terms_agreed', local_terms_agreed)" id="merchant-terms-agreed" v-model="local_terms_agreed">
                        <label class="form-check-label" for="merchant-terms-agreed">
                            Terms & Agreements
                        </label>
                    </div>
                </div>
                <div class="col-12 col-sm-4 mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" @change="$emit('propogate_data', 'welcome_email', local_welcome_email)" id="merchant-welcome-email" v-model="local_welcome_email">
                        <label class="form-check-label" for="merchant-welcome-email">
                            Welcome Email (videos)
                        </label>
                    </div>
                </div>
                <div class="col-12 col-sm-4 mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" @change="$emit('propogate_data', 'go_live_text', local_go_live_text)" id="merchant-go-live-text" v-model="local_go_live_text">
                        <label class="form-check-label" for="merchant-go-live-text">
                            Go Live Text
                        </label>
                    </div>
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
                    <label for="merchant-new-note" class="form-label">New Note</label>
                    <textarea class="form-control" id="merchant-new-note" rows="3" v-model="new_note"></textarea>
                    <br>
                    <button type="button" class="w-100 btn btn-primary btn-block rounded-pill text-white" @click="submit_note()">Save</button>                
                </div>            
            </div>
        </div>
    `
});

Vue.component('merchant-images', {
    props: ['images', 'merchant_id'],
    data: function() {
        return {
            dropzone: null,
            complete: false,
            progress: 0,
            timeout: null,
            uploading: false,
            upload_error: false,
            error: false
        }
    },
    methods: {
        upload_file: function(file) {
            let key = `merchant-${this.merchant_id}/${file.name}`;
            var params = {
                Body: file,
                ContentType: file.type,
                Key: key,
                Bucket: bucket,
                ACL: 'public-read'
            };

            window.onbeforeunload = function() {
                return 'Leaving this page will stop the upload and will not save your changes.';
            };

            this.uploading = true;
            let upload = this;
            s3.upload(params).on('httpUploadProgress', function(evt) {
                let p = (evt.loaded * 100) / evt.total;
                upload.progress = Math.trunc(p);
            }).send(function(err, data) {
                window.onbeforeunload = null;
                $(upload.$el).find(`.dropzone`)[0].dropzone.removeAllFiles(true);
                if (data && data.Location) {
                    console.log(data);
                    if (!merchants.active_merchant.images) {
                        merchants.active_merchant.images = [];
                    }
                    merchants.active_merchant.images.push(data.Location);
                    merchants.trigger_save(0);
                    upload.progress = 100;
                    upload.complete = true;
                    upload.uploading = false;
                } else {
                    upload.upload_error = true;
                    upload.progress = 0;
                    upload.uploading = false;
                }
            });
        }
    },
    mounted: function() {
        let el = $(this.$el);
        let upload = this;

        this.$nextTick(function () {
            let options = {
                uploadMultiple: false,  //upload multiple files
                maxFilesize: 2048,
                acceptedFiles: ".jpeg,.jpg,.png,.gif",
                accept (file, done) {
                    upload.upload_file(file)
                },
                addedfile: function(file) {
                    let type = file.type.split('/')[1];
                    let allowed = ['jpg', 'jpeg', 'gif', 'png'];
                    if (allowed.indexOf(type) === -1) {
                        upload.error = true;
                    } else {
                        upload.error = false;
                        file.previewElement = Dropzone.createElement(this.options.previewTemplate);
                    }
                }
            };

            el.find(".dropzone").dropzone(options);
        });
    },
    template: `
        <div class="merchant-images gilroy">
            <div class="mb-3 pb-3 border-bottom d-flex flex-row flex-wrap">
                <div v-if="!images || images.length === 0" class="font-md text-muted w-100 text-center">- No Images -</div>
                <div v-for="(image, i) in images" class="image-wrapper mx-2">
                    <img class="rounded-3" v-bind:src="image" style="width: 100%; height: auto; max-height: 150px; max-width: 200px;">
                </div>
            </div>
            <div class="form-group mt-3">
                <form action="/" class="dropzone rounded">
                    <div class="dz-message" data-dz-message>
                        <div v-if="!uploading" class="w-100 px-2 px-md-5 text-center position-relative">
                            <span class="title d-block mb-2">Drag files or click here for upload</span>
                            <span v-if="complete" class="complete">File successfully uploaded.</span>
                            <span v-if="!uploading && !complete" class="subtitle">Image files only (Max files size: 2GB)</span>
                            <span v-if="error" class="error">Valid file types include JPG, GIF, and PNG</span>
                            <span v-if="upload_error" class="upload-error">An error occurred. Please refresh the page and try again.</span>
                        </div>
                        <div v-if="uploading" class="w-100 px-2 px-md-5 text-center upload-progress">
                            <span v-if="uploading" class="title d-block">Uploading</span>
                            <div class="progress w-100">
                                <div class="progress-bar"  role="progressbar" v-bind:style="'width: ' + (uploading ? progress : '100') + '%'" v-bind:aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                        </div>
                     </div>
                </form>
            </div>
        </div>
`
});

Vue.component('merchant-offers', {
    props: ['offers'],
    data: function() {
        return {
            current_offer: null,
            current_index: null,
            single_use: false,
            happy_hour: false,
            all_day: false,
            happy_hour_index: 0,
            days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        }
    },
    computed: {
    },
    methods: {
        get_offer_type: function(offer) {
            let offer_type = 'All Day';
            if (offer.single_use) {
                offer_type = 'One Time';
            }
            if (offer.happy_hour) {
                offer_type = 'Happy Hour';
            }
            return offer_type
        },
        edit_offer: function(offer, i) {
            this.current_offer = offer;
            this.current_index = i;

            this.single_use = offer.single_use;
            this.happy_hour = offer.happy_hour;
            this.all_day = !offer.single_use && !offer.happy_hour;

            if (!this.current_offer.hours || this.current_offer.hours.length !== 7) {
                this.current_offer.hours = [
                    [], // Monday
                    [], // Tuesday
                    [], // Wednesday
                    [], // Thursday
                    [], // Friday
                    [], // Saturday
                    [], // Sunday
                ]
            }

            $("#modal-offer-edit").modal('show');
            $(".custom-backdrop").fadeIn();
            this.set_inputmask();
        },
        done_editing: function() {
            this.current_offer = null;
            this.current_index = null;
            $("#modal-offer-edit").modal('hide');
            $(".custom-backdrop").fadeOut();
        },
        set_offer_type: function(type) {
            this.all_day = type === 'all-day';
            this.happy_hour = type === 'happy-hour';
            this.single_use = type === 'one-time';

            this.current_offer.happy_hour = type === 'happy-hour';
            this.current_offer.single_use = type === 'one-time';

            this.$emit('save_offer', this.current_offer, this.current_index);
        },
        delete_slot: function(i, j) {
            console.log(i);
            console.log(j);
            console.log(this.current_offer.hours[i]);
            this.current_offer.hours[i].splice(j, 1);
            this.$emit('save_offer', this.current_offer, this.current_index);
        },
        new_slot: function(i) {
            console.log(this.current_offer.hours);
            this.current_offer.hours[i].push({start: null, end: null});
            this.set_inputmask();

            this.$emit('save_offer', this.current_offer, this.current_index);
        },
        set_inputmask: function() {
            let settings = this;
            this.$nextTick(function() {
                $(".im-time").inputmask("9{1,2}:9{2} XM", {
                    definitions: {
                        "X": {
                            validator: "[aA]|[pP]",
                            casing: "upper"
                        }
                    },
                    oncomplete: function() {
                        let ipt = $(this);
                        let val = ipt.val();
                        let i = ipt.data('i');
                        let j = ipt.data('j');
                        let when = ipt.data('when');
                        settings.current_offer.hours[i][j][when] = val;
                        settings.$emit('save_offer', settings.current_offer, settings.current_index);
                    }
                });
            });
        }
    },
    template: `
        <div class="merchant-offers gilroy position-relative">
            <div class="my-3 d-flex flex-row justify-content-end">
                <button type="button" @click="$emit('new_offer')" class="btn btn-primary px-4 text-white">+ New Offer</button>
            </div>
            <table id="table-merchant-offers" class="w-100" style="border-collapse: separate; border-spacing: 0 10px">
                <tr class="bg-transparent p-3">
                    <th class="text-secondary font-md p-2">Offer</th>
                    <th class="text-secondary font-md p-2">Type</th>
                    <th class="text-secondary font-md p-2">Redemptions</th>
                    <th class="text-secondary font-md p-2"></th>
                </tr>
                <tr v-if="!offers || offers.length === 0">
                    <td colspan="4" class="border rounded-3 py-2 bg-white text-center text-black-50 font-sm">No results found</td>
                </tr>
                <tr v-for="(offer, i) in offers">
                    <td class="text-primary ` + td_start + `">{{ offer.offer ? offer.offer : 'New Offer' }}</td>
                    <td class="` + td_middle + `">{{ get_offer_type(offer) }}</td>
                    <td class="` + td_middle + `">{{ offer.redemptions ? offer.redemptions : 0 }}</td>
                    <td class="offer-controls ` + td_end + `" style="width: 200px;">
                        <i class="btn btn-success fas fa-pencil-alt text-white me-2" @click="edit_offer(offer, i)"></i> 
                        <i class="btn btn-danger fas fa-trash-alt" @click="$emit('delete_offer', offer, i)"></i>
                    </td>
                </tr>
            </table>
            
            <div id="modal-offer-edit" class="modal" tabindex="-1" style="z-index: 1052;" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Edit Offer</h5>
                        </div>
                        <div class="modal-body">
                            <div v-if="current_offer" class="row">
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="offer-offer" class="form-label">Offer</label>
                                    <input type="text" class="form-control" id="offer-offer" v-model="current_offer.offer" v-on:input="$emit('save_offer', current_offer, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="offer-details" class="form-label">Details</label>
                                    <input type="text" class="form-control" id="offer-details" v-model="current_offer.details" v-on:input="$emit('save_offer', current_offer, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="offer-value" class="form-label">Est. Value of Discount</label>
                                    <input type="text" class="form-control" id="offer-value" v-model="current_offer.value" v-on:input="$emit('save_offer', current_offer, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="offer-deal-limit" class="form-label">Min. Purchase to Redeem</label>
                                    <input type="text" class="form-control" id="offer-deal-limit" v-model="current_offer.deal_limit" v-on:input="$emit('save_offer', current_offer, current_index)">
                                </div>
                                <div class="col-12 col-sm-3 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" @change="set_offer_type('all-day')" id="offer-all-day" v-model="all_day">
                                        <label class="form-check-label" for="offer-all-day">
                                            All Day
                                        </label>
                                    </div>
                                </div>
                                <div class="col-12 col-sm-3 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" @change="set_offer_type('happy-hour')" id="offer-happy-hour" v-model="happy_hour">
                                        <label class="form-check-label" for="offer-happy-hour">
                                            Happy Hour
                                        </label>
                                    </div>
                                </div>
                                <div class="col-12 col-sm-3 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" @change="set_offer_type('one-time')" id="offer-one-time" v-model="single_use">
                                        <label class="form-check-label" for="offer-one-time">
                                            One Time
                                        </label>
                                    </div>
                                </div>
                                <div class="col-12 col-sm-3 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" v-model="current_offer.is_bogo" @click="$emit('save_offer', current_offer, current_index)" id="offer-is-bogo">
                                        <label class="form-check-label" for="offer-is-bogo">
                                            BOGO
                                        </label>
                                    </div>
                                </div>
                                <div v-if="current_offer.happy_hour" class="mt-3">
                                    <h5>Happy Hour Time Slots</h5>
                                    <ul class="nav nav-tabs">
                                        <li class="nav-item" v-for="(day, i) in days" v-bind:key="day.toLowerCase()">
                                            <a class="nav-link" v-bind:class="{'active': happy_hour_index === i}" aria-current="page" href="#" @click="happy_hour_index = i">{{ day }}</a>
                                        </li>
                                    </ul>
                                    <div class="mb-3 pt-3" v-for="(day, i) in days" v-bind:key="day.toLowerCase() + '-settings'" v-if="happy_hour_index === i">
                                        <div class="d-flex flex-row justify-content-end">
                                            <button type="button" @click="new_slot(i)" class="btn btn-primary px-4 text-white float-right">+ New Time Slot</button>
                                        </div>
                                        <div class="row mb-2" v-for="(slot, j) in current_offer.hours[i]">
                                            <div class="col-5">
                                                <label class="form-label">Start</label>
                                                <input type="text" class="form-control im-time" v-bind:value="slot.start" v-bind:data-i="i" v-bind:data-j="j" v-bind:data-when="'start'">
                                            </div>
                                            <div class="col-5">
                                                <label class="form-label">End</label>
                                                <input type="text" class="form-control im-time" v-bind:value="slot.end" v-bind:data-i="i" v-bind:data-j="j" v-bind:data-when="'end'">
                                            </div>
                                            <div class="col-2 font-md text-danger">
                                                <label class="form-label">&nbsp;</label><br>
                                                <i class="fas fa-minus-circle cursor-pointer pt-1" @click="delete_slot(i, j)"></i>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-12 pt-3 border-top">
                                    <h5>Online Code Settings</h5>
                                    <p class="font-sm text-muted">If a redemption code is set (i.e. PASS360TWENTY) then it will be texted to the user after they redeem in the app. The 'Where To Redeem URL' is the link to the company's website or online location to enter the promo code.</p>
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="offer-code" class="form-label">Redemption Code</label>
                                    <input type="text" class="form-control" id="offer-code" v-model="current_offer.code" v-on:input="$emit('save_offer', current_offer, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="offer-code-link" class="form-label">Where To Redeem URL</label>
                                    <input type="text" class="form-control" id="offer-code-link" v-model="current_offer.code_link" v-on:input="$emit('save_offer', current_offer, current_index)">
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary text-white" @click="done_editing()">Done</button>
                        </div>
                    </div>
                </div>
            </div>            
        </div>
    `
});

Vue.component('merchant-locations', {
    props: ['locations'],
    data: function() {
        return {
            current_location: null,
            current_index: null,
            new_note: ''
        }
    },
    methods: {
        edit_location: function(location, i) {
            this.current_location = location;
            this.current_index = i;

            $("#modal-location-edit").modal('show');
            $(".custom-backdrop").fadeIn();
        },
        done_editing: function() {
            this.current_location = null;
            this.current_index = null;
            $("#modal-location-edit").modal('hide');
            $(".custom-backdrop").fadeOut();
        },
        submit_note: function() {
            if (this.current_location !== null) {
                this.$emit('new_note', this.new_note, this.current_location.id);
                this.new_note = '';
            }
        }
    },
    template: `
        <div class="merchant-locations gilroy position-relative">
            <div class="my-3 d-flex flex-row justify-content-end">
                <button type="button" @click="$emit('new_location')" class="btn btn-primary px-4 text-white">+ New Location</button>
            </div>
            <table id="table-merchant-locations" class="w-100" style="border-collapse: separate; border-spacing: 0 10px">
                <tr class="bg-transparent p-3">
                    <th class="text-secondary font-md p-2">Address</th>
                    <th class="text-secondary font-md p-2">City</th>
                    <th class="text-secondary font-md p-2">Zip</th>
                    <th class="text-secondary font-md p-2">Phone</th>
                    <th class="text-secondary font-md p-2"></th>
                </tr>
                <tr v-if="!locations || locations.length === 0">
                    <td colspan="4" class="border rounded-3 py-2 bg-white text-center text-black-50 font-sm">No results found</td>
                </tr>
                <tr v-for="(location, i) in locations">
                    <td class="` + td_start + `">{{ location.address ? location.address : 'New Location'}}{{ location.address2 ? ' ' + location.address2 : ''  }}</td>
                    <td class="` + td_middle + `">{{ location.city }}{{ location.state ? ', ' + location.state : ''  }}</td>
                    <td class="` + td_middle + `">{{ location.zip_code }}</td>
                    <td class="` + td_middle + `">{{ location.phone }}</td>
                    <td class="location-controls ` + td_end + `" style="width: 200px;">
                        <i class="btn btn-success fas fa-pencil-alt text-white me-2" @click="edit_location(location, i)"></i> 
                        <i class="btn btn-danger fas fa-trash-alt" @click="$emit('delete_location', location, i)"></i>
                    </td>
                </tr>
            </table>
            
            <div id="modal-location-edit" class="modal" tabindex="-1" style="z-index: 1052;" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Edit Location</h5>
                        </div>
                        <div class="modal-body">
                            <div v-if="current_location" class="row">
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="location-address" class="form-label">Address</label>
                                    <input type="text" class="form-control" id="location-address" v-model="current_location.address" v-on:input="$emit('save_location', current_location, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="location-address2" class="form-label">Address Line 2</label>
                                    <input type="text" class="form-control" id="location-address2" v-model="current_location.address2" v-on:input="$emit('save_location', current_location, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="location-city" class="form-label">City</label>
                                    <input type="text" class="form-control" id="location-city" v-model="current_location.city" v-on:input="$emit('save_location', current_location, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="location-state" class="form-label">State</label>
                                    <input type="text" class="form-control" id="location-state" v-model="current_location.state" v-on:input="$emit('save_location', current_location, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="location-zip" class="form-label">Zip code</label>
                                    <input type="text" class="form-control" id="location-zip" v-model="current_location.zip_code" v-on:input="$emit('save_location', current_location, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="location-phone" class="form-label">Phone</label>
                                    <input type="text" class="form-control" id="location-phone" v-model="current_location.phone" v-on:input="$emit('save_location', current_location, current_index)">
                                </div>
                                <div class="col-6 p-2">
                                    <div v-if="!current_location.notes || current_location.notes.length === 0" class="w-100 text-center text-muted">
                                        - No notes -
                                    </div>
                                    <div v-for="(note, i) in current_location.notes">
                                        <p class="mb-0">{{ note.note }}</p>
                                        <div class="d-flex justify-content-between align-content-center mb-2 font-sm">
                                            <span class="text-muted">{{ note.created }}</span>
                                            <i class="fas fa-trash-alt text-danger cursor-pointer" @click="$emit('delete_note', note, i, current_location.id)"></i>
                                        </div>
                                    </div>
                                </div>            
                                <div class="col-6 p-2">
                                    <label for="location-new-note" class="form-label">New Note</label>
                                    <textarea class="form-control" id="location-new-note" rows="3" v-model="new_note"></textarea>
                                    <br>
                                    <button type="button" class="w-100 btn btn-primary btn-block rounded-pill text-white" @click="submit_note()">Save</button>                
                                </div>            
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary text-white" @click="done_editing()">Done</button>
                        </div>
                    </div>
                </div>
            </div>            
        </div>
    `
});

Vue.component('merchant-contacts', {
    props: ['contacts'],
    data: function() {
        return {
            current_contact: null,
            current_index: null
        }
    },
    methods: {
        edit_contact: function(contact, i) {
            this.current_contact = contact;
            this.current_index = i;

            $("#modal-contact-edit").modal('show');
            $(".custom-backdrop").fadeIn();
        },
        done_editing: function() {
            this.current_contact = null;
            this.current_index = null;
            $("#modal-contact-edit").modal('hide');
            $(".custom-backdrop").fadeOut();
        }
    },
    template: `
        <div class="merchant-contacts gilroy position-relative">
            <div class="my-3 d-flex flex-row justify-content-end">
                <button type="button" @click="$emit('new_contact')" class="btn btn-primary px-4 text-white">+ New contact</button>
            </div>
            <table id="table-merchant-contacts" class="w-100" style="border-collapse: separate; border-spacing: 0 10px">
                <tr class="bg-transparent p-3">
                    <th class="text-secondary font-md p-2">Name</th>
                    <th class="text-secondary font-md p-2">Phone</th>
                    <th class="text-secondary font-md p-2"></th>
                </tr>
                <tr v-if="!contacts || contacts.length === 0">
                    <td colspan="4" class="border rounded-3 py-2 bg-white text-center text-black-50 font-sm">No results found</td>
                </tr>
                <tr v-for="(contact, i) in contacts">
                    <td class="text-primary ` + td_start + `">{{ contact.name ? contact.name : 'New Contact' }}</td>
                    <td class="` + td_middle + `">{{ contact.phone }}</td>
                    <td class="contact-controls ` + td_end + `" style="width: 200px;">
                        <i class="btn btn-success fas fa-pencil-alt text-white me-2" @click="edit_contact(contact, i)"></i> 
                        <i class="btn btn-danger fas fa-trash-alt" @click="$emit('delete_contact', contact, i)"></i>
                    </td>
                </tr>
            </table>
            
            <div id="modal-contact-edit" class="modal" tabindex="-1" style="z-index: 1052;" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Edit Contact</h5>
                        </div>
                        <div class="modal-body">
                            <div v-if="current_contact" class="row">
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="contact-name" class="form-label">Name</label>
                                    <input type="text" class="form-control" id="contact-name" v-model="current_contact.name" v-on:input="$emit('save_contact', current_contact, current_index)">
                                </div>
                                <div class="col-12 col-sm-6 mb-2">
                                    <label for="contact-phone" class="form-label">Phone</label>
                                    <input type="text" class="form-control" id="contact-phone" v-model="current_contact.phone" v-on:input="$emit('save_contact', current_contact, current_index)">
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary text-white" @click="done_editing()">Done</button>
                        </div>
                    </div>
                </div>
            </div>            
        </div>
    `
});