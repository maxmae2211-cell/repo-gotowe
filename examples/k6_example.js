import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
    vus: 10,
    duration: '1m',
};

export default function () {
    // GET posts
    let res = http.get('https://jsonplaceholder.typicode.com/posts');
    check(res, {
        'status 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    sleep(0.5);

    // GET single user
    let res2 = http.get('https://jsonplaceholder.typicode.com/users/1');
    check(res2, {
        'status 200': (r) => r.status === 200,
    });
    sleep(0.5);
}
