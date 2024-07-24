from django.utils.translation import gettext as _

class Messages:
    # Jwt
    JWT_SUCCESS = _('Success')
    JWT_INAVLID_TOKEN = _('Invalid token provided')
    JWT_EXPIRED_TOKEN = _('Session expired, Please login')

    # General
    SUCCESS = _('Success')
    ERROR = _('Some error occurred, Please try again later')
    ERROR_TOKEN = _('Invalid token passed, or token has expired')
    ERROR_ACCOUNT_INACTIVE = _('Your account has been deleted, Please contact support')
    ERROR_ACCOUNT_EXISTS = _('Account with this email already exists, Please try to login')

    # Upvote Incident
    SUCCESS_UPVOTE = _('You have successfully upvoted the issue')
    ERROR_ALREADY_UPVOTED = _('You have already upvoted this issue')
    ERROR_INVALID_INCIDENT_ID = _('Invalid issue ID')

    # Delete Incident
    SUCCESS_DELETE = _('Issue deleted successfully')
    ERROR_DELETE = _('Issue cannot be deleted at this point')

    # Report
    SUCCESS_REPORT = _('You have successfully reported the issue')
    ERROR_INVALID_CATEGORY_ID = _('Invalid issue category ID')

    # User
    ERROR_INVALID_FILTERBY = _('Invalid filter option provided')

    # Site
    ERROR_INVALID_REPORTEDBY = _('Invalid reported by option provided')
    ERROR_INVALID_STATUS = _('Invalid status option passed')
    ERROR_NO_PROJECT = _('No project is associated with your account')
    ERROR_ALREADY_IN_STATUS = _('Issue is already in a state of given status')
    ERROR_UNAUTHORIZED = _('You are unauthorized to make this request')
    ERROR_UNAUTHORIZED_RESOLVE = _('You are unauthorized to resolve the issue as it doesnot belong to your project')
    ERROR_UNAUTHORIZED_REJECT = _('You are unauthorized to reject the issue as it doesnot belong to your project')

class NotificationMessages:
    NEARBY_REPORT = _('A issue was reported nearby you')
    NEARBY_REPORT_CONFIRMED = _('A issue was confirmed nearby you')
    USER_UPVOTED_REPORT = _('{0} upvoted your report')
    UPVOTE_THRESHOLD_REPORT = _('Your report is now pending action')
    ORG_RESOLVED_REPORT = _('{0} has resolved your report')
    ORG_REJECTED_REPORT = _('{0} has rejected your report')
    ORG_ACCEPTED_REPORT = _('{0} has accepted your report')
