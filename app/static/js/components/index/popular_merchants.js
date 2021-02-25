Vue.component('explore-option', {
    props: ['title', 'image', 'id'],
    template: `
        <div class="explore-option position-relative">
            <button type="button" class="font-md border-0 position-absolute bg-white text-dark px-5 rounded-pill cursor-pointer" @click="$emit('select_option', id)">Explore</button>
            <h5 class="font-lg text-dark mb-2 gilroy-bold">{{ title }}</h5>
            <img v-bind:src="image">
        </div>
    `
});

Vue.component('merchant', {
    props: ['image', 'name', 'city', 'state'],
    template: `
        <div class="mt-2 gilroy border-light rounded shadow-sm">
            <div class="col-4">
                <img class="img-fluid w-100 rounded-left" v-bind:src="image" v-bind:alt="name" style="height: 80px; object-fit: cover;">
            </div>
            <div class="col-8 px-2 pt-3">
                <h5 class="m-0 card-title">{{ name }}</h5>
                <p class="text-muted"><i class="fas fa-map-marker-alt"></i> {{ city }}, {{ state }}</p>
            </div>
        </div>
    `
});
