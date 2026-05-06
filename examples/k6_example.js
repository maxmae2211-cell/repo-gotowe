import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
    stages: [
        { duration: '20s', target: 5 },
        { duration: '40s', target: 15 },
        { duration: '30s', target: 15 },
        { duration: '20s', target: 0 },
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'],
        http_req_duration: ['p(95)<1200', 'p(99)<2000'],
    },
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
