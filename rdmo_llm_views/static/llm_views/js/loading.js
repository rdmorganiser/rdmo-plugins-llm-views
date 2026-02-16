const handlePolling = (project_id, snapshot_id, view_id, timeout) => {
    setTimeout(() => {
        const baseUrl = document.querySelector('meta[name="baseurl"]').content.replace(/\/+$/, '')
        const url = `${baseUrl}/api/v1/llm-views/projects/${project_id}/status/`

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Cookies.get('csrftoken')
            },
            body: JSON.stringify({
                snapshot: snapshot_id,
                view: view_id
            })
        }).then((response) => response.json()).then((status) => {
            if (status.done) {
                location.reload()
            } else {
                handlePolling(project_id, snapshot_id, view_id, timeout)
            }
        })
    }, timeout)
}
