"""
    Tools for dealing with wp_paste objects.
    -Christopher Welborn 1-3-17
"""


def get_paste_children(paste, order_by='-publish_date'):
    """ Get paste children, handling private replies. """
    filterargs = {'disabled': False}
    if not paste.private:
        # Don't show private replies for public pastes.
        filterargs['private'] = False

    # Use ids at first, running is_expired(). No content needed for this.
    children_ids = set(
        p.id
        for p in paste.children.defer('content').filter(**filterargs)
        if not p.is_expired()
    )
    # Convert back into QuerySet using filter and children_ids.
    children = paste.children.filter(id__in=children_ids)
    if order_by:
        return children.order_by(order_by)
    return children


def get_paste_parent(paste):
    """ Get a paste's parent, if it is not disabled.
        A private parent is only viewable if the child (`paste`) is private
        also.
    """
    if not paste.parent:
        return None
    if paste.parent.disabled:
        return None
    if paste.parent.private:
        if paste.private:
            # Okay, because both are private.
            return paste.parent
        # No okay. Public paste looking for a private parent.
        return None
    # Parent is not private and not disabled.
    if paste.parent.is_expired():
        return None
    return paste.parent
