import http from 'k6/http';
import { check } from 'k6';

export const options = {
    vus: 20,
    duration: '30s',
};

export function setup() {
    const acmeLogin = http.post('http://acme.localhost:8000/api/token/',
        JSON.stringify({ username: 'acme_agent', password: 'testpass123' }),
        { headers: { 'Content-Type': 'application/json', Host: 'acme.localhost' } }
    );
    const globexLogin = http.post('http://globex.localhost:8000/api/token/',
        JSON.stringify({ username: 'globex_agent', password: 'testpass123' }),
        { headers: { 'Content-Type': 'application/json', Host: 'globex.localhost' } }
    );

    check(acmeLogin, { 'acme login succeeded': (r) => r.status === 200 });
    check(globexLogin, { 'globex login succeeded': (r) => r.status === 200 });

    return {
        acmeToken: acmeLogin.json('access'),
        globexToken: globexLogin.json('access'),
    };
}

export default function (data) {
    const acmeRes = http.get('http://acme.localhost:8000/api/tickets/', {
        headers: {
            Host: 'acme.localhost',
            Authorization: `Bearer ${data.acmeToken}`,
        },
    });

    const globexRes = http.get('http://globex.localhost:8000/api/tickets/', {
        headers: {
            Host: 'globex.localhost',
            Authorization: `Bearer ${data.globexToken}`,
        },
    });

    check(acmeRes, { 'acme status 200': (r) => r.status === 200 });
    check(globexRes, { 'globex status 200': (r) => r.status === 200 });
}