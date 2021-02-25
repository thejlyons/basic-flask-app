const td_start = 'bg-white rounded-start border border-end-0 py-2 px-3';
const td_middle = 'bg-white border-top border-bottom p-2 pl-4';
const td_end = 'bg-white border border-start-0 rounded-end py-2 pl-4';

Vue.component('fundraiser', {
    props: ['fundraiser'],
    template: `
        <tr class="fundraiser-row gilroy">
            <td>
                <div v-if="fundraiser.from_form" style="width: 30px;">
                    <div class="spinner-grow text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </td>
            <td class="fundraiser-team-code text-primary ` + td_start + `">
                <h5>{{ fundraiser.team_code ? fundraiser.team_code : 'New fundraiser' }}</h5>
            </td>
            <td class="fundraiser-code ` + td_middle + `">{{ fundraiser.code }}</td>
            <td class="fundraiser-today ` + td_middle + `">0</td>
            <td class="fundraiser-total ` + td_middle + `">0</td>
            <td class="fundraiser-goal ` + td_middle + `">\${{ fundraiser.base_goal }}</td>
            <td class="fundraiser-start ` + td_middle + `">{{ fundraiser.start ? fundraiser.start.replace(' 00:00:00 GMT', '') : '' }}</td>
            <td class="fundraiser-expiration ` + td_middle + `">{{ fundraiser.expiration ? fundraiser.expiration.replace(' 00:00:00 GMT', '') : '' }}</td>
            <td class="fundraiser-incentives ` + td_middle + `">
                <div class="my-2 me-3" style="height: 60px;">
                    <img v-if="fundraiser.incentives" class="rounded-3" v-bind:src="fundraiser.incentives" style="max-width:100%; max-height:100%;">
                </div>
            </td>
            <td class="fundraiser-controls ` + td_end + `">
                <i class="btn btn-success fas fa-pencil-alt text-white me-2" @click="$emit('set_active', fundraiser)"></i> 
                <i class="btn btn-danger fas fa-trash-alt" @click="$emit('delete_fundraiser', fundraiser)"></i> 
            </td>
        </tr>
    `
});

Vue.component('fundraiser-settings', {
    props: ['team_code', 'code', 'base_goal', 'start', 'expiration', 'from_form', 'active', 'notes'],
    data: function() {
        return {
            'local_team_code': this.team_code,
            'local_code': this.code,
            'local_base_goal': this.base_goal,
            'local_start': this.start,
            'local_expiration': this.expiration,
            'approved': !this.from_form,
            'local_active': this.active,
            'new_note': ''
        }
    },
    mounted: function() {
        this.set_inputmask();
    },
    methods: {
        submit_note: function() {
            this.$emit('new_note', this.new_note);
            this.new_note = '';
        },
        set_inputmask: function() {
            let settings = this;
            this.$nextTick(function() {
                $(".im-date-fund").inputmask({
                    'alias': 'datetime',
                    'inputFormat': 'dd/MM/yyyy',
                    'inputMode': 'numeric',
                    oncomplete: function() {
                        let ipt = $(this);
                        let val = ipt.val();
                        let when = ipt.data('when');
                        if (when === 'start') {
                            settings.local_start = val;
                            settings.$emit('propogate_data', 'start', settings.local_start)
                        } else {
                            settings.local_expiration = val;
                            settings.$emit('propogate_data', 'expiration', settings.local_expiration)
                        }
                    }
                });
            });
        },
        update_approved: function() {
            this.$nextTick(function() {

            });
        }
    },
    template: `
        <div class="fundraiser-settings gilroy">
            <div class="mb-3">
                <label for="fundraiser-team-code" class="form-label">Organization Name</label>
                <input type="text" class="form-control" id="fundraiser-team-code" v-model="local_team_code" v-on:input="$emit('propogate_data', 'team_code', local_team_code)">
            </div>
            <div class="row mb-3 border-bottom pb-4">
                <div class="col-12 col-md-6">
                    <label for="fundraiser-code" class="form-label">Code</label>
                    <input type="text" class="form-control" id="fundraiser-code" v-model="local_code" v-on:input="$emit('propogate_data', 'code', local_code)">
                </div>
                <div class="col-12 col-md-6">
                    <label for="fundraiser-base-goal" class="form-label">Base Goal</label>
                    <input type="text" class="form-control" id="fundraiser-base-goal" v-model="local_base_goal" v-on:input="$emit('propogate_data', 'base_goal', local_base_goal)">
                </div>
                <div class="col-12 col-md-6">
                    <label for="fundraiser-start" class="form-label">Start</label>
                    <input type="text" class="form-control im-date-fund" id="fundraiser-start" v-model="local_start" data-when="start">
                </div>
                <div class="col-12 col-md-6">
                    <label for="fundraiser-expiration" class="form-label">Expiration</label>
                    <input type="text" class="form-control im-date-fund" id="fundraiser-expiration" v-model="local_expiration" data-when="expiration">
                </div>
                <div class="col-12 col-sm-6 mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" v-model="approved" @change="$emit('propogate_data', 'from_form', !approved)" id="fundraiser-approved">
                        <label class="form-check-label" for="fundraiser-approved">
                            Approved
                        </label>
                    </div>
                </div>
                <div class="col-12 col-sm-6 mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" v-model="local_active" @change="$emit('propogate_data', 'active', local_active)" id="fundraiser-active">
                        <label class="form-check-label" for="fundraiser-active">
                            Active
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
                    <label for="fundraiser-new-note" class="form-label">New Note</label>
                    <textarea class="form-control" id="fundraiser-new-note" rows="3" v-model="new_note"></textarea>
                    <br>
                    <button type="button" class="w-100 btn btn-primary btn-block rounded-pill text-white" @click="submit_note()">Save</button>                
                </div>            
            </div>
        </div>
    `
});

Vue.component('fundraiser-incentive', {
    props: ['incentive', 'fundraiser_id'],
    data: function() {
        return {
            local_incentive: this.incentive,
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
            let key = `fundraiser-${this.fundraiser_id}/${file.name}`;
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
                    fundraisers.active_fundraiser.incentives = data.Location;
                    upload.local_incentive = data.Location;
                    upload.$emit('propogate_data', 'incentives', data.Location);
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
        <div class="fundraiser-images gilroy">
            <div class="mb-3 pb-3 border-bottom d-flex flex-row flex-wrap">
                <div v-if="!local_incentive" class="font-md text-muted w-100 text-center">- No Incentive -</div>
                <div v-else class="image-wrapper mx-2">
                    <img class="rounded-3" v-bind:src="local_incentive" style="width: 100%; height: auto; max-height: 250px; max-width: 300px;">
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

Vue.component('fundraiser-contact', {
    props: ['name', 'email', 'phone', 'city', 'state'],
    data: function() {
        return {
            'local_name': this.name,
            'local_email': this.email,
            'local_phone': this.phone,
            'local_city': this.city,
            'local_state': this.state
        }
    },
    methods: {
    },
    template: `
        <div class="fundraiser-settings gilroy">
            <div class="mb-3">
                <label for="fundraiser-name" class="form-label">Contact Name</label>
                <input type="text" class="form-control" id="fundraiser-name" v-model="local_name" v-on:input="$emit('propogate_data', 'contact_name', local_name)">
            </div>
            <div class="row mb-3 border-bottom pb-4">
                <div class="col-12 col-md-6 mb-2">
                    <label for="fundraiser-email" class="form-label">Email</label>
                    <input type="text" class="form-control" id="fundraiser-email" v-model="local_email" v-on:input="$emit('propogate_data', 'contact_email', local_email)">
                </div>
                <div class="col-12 col-md-6 mb-2">
                    <label for="fundraiser-phone" class="form-label">Phone</label>
                    <input type="text" class="form-control" id="fundraiser-phone" v-model="local_phone" v-on:input="$emit('propogate_data', 'contact_phone', local_phone)">
                </div>
                <div class="col-12 col-md-6 mb-2">
                    <label for="fundraiser-city" class="form-label">City</label>
                    <input type="text" class="form-control" id="fundraiser-city" v-model="local_city" v-on:input="$emit('propogate_data', 'city', local_city)">
                </div>
                <div class="col-12 col-md-6 mb-2">
                    <label for="fundraiser-state" class="form-label">State</label>
                    <input type="text" class="form-control" id="fundraiser-state" v-model="local_state" v-on:input="$emit('propogate_data', 'state', local_state)">
                </div>
            </div>
        </div>
    `
});